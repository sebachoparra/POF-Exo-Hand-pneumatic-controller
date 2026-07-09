#include <atomic>
#include <chrono>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
#include <vector>

#include "rcl_interfaces/msg/set_parameters_result.hpp"
#include "rclcpp/rclcpp.hpp"

#include "hyperion_ros2_driver/msg/hyperion_peaks.hpp"
#include "hLibrary.h"

namespace
{

constexpr int kHyperionChannelCount = H_MAX_NUM_CHANNELS;

struct HyperionPeakSample
{
  uint64_t serial = 0;
  double instrument_timestamp = 0.0;
  std::vector<uint32_t> peak_counts;
  std::vector<double> wavelengths;
};

std::chrono::nanoseconds period_from_rate(double rate_hz)
{
  const auto period = std::chrono::duration<double>(1.0 / rate_hz);
  return std::chrono::duration_cast<std::chrono::nanoseconds>(period);
}

}  // namespace

class HyperionDriverNode : public rclcpp::Node
{
public:
  HyperionDriverNode()
  : Node("hyperion_driver_node")
  {
    interrogator_ip_ = declare_parameter<std::string>("interrogator_ip", "10.0.0.55");
    publish_rate_hz_ = declare_parameter<double>("publish_rate_hz", 100.0);
    stream_divider_ = declare_parameter<int>("stream_divider", 1);
    frame_id_ = declare_parameter<std::string>("frame_id", "hyperion");

    if (publish_rate_hz_ <= 0.0) {
      throw std::runtime_error("publish_rate_hz must be greater than zero");
    }
    if (stream_divider_ < 1) {
      throw std::runtime_error("stream_divider must be greater than or equal to 1");
    }

    publisher_ = create_publisher<hyperion_ros2_driver::msg::HyperionPeaks>(
      "hyperion/peaks", rclcpp::SensorDataQoS());

    parameter_callback_handle_ = add_on_set_parameters_callback(
      std::bind(&HyperionDriverNode::onParametersChanged, this, std::placeholders::_1));

    configurePublishTimer(publish_rate_hz_);
    startAcquisitionThread();
  }

  ~HyperionDriverNode() override
  {
    stopAcquisitionThread();
  }

private:
  void startAcquisitionThread()
  {
    stop_requested_.store(false);
    acquisition_thread_ = std::thread(&HyperionDriverNode::acquisitionLoop, this);
  }

  void stopAcquisitionThread()
  {
    stop_requested_.store(true);

    {
      std::lock_guard<std::mutex> lock(hyperion_mutex_);
      if (active_hyperion_ != nullptr) {
        try {
          active_hyperion_->close_comm();
        } catch (const std::exception & e) {
          RCLCPP_WARN(get_logger(), "Error while closing Hyperion sockets: %s", e.what());
        } catch (...) {
          RCLCPP_WARN(get_logger(), "Unknown error while closing Hyperion sockets");
        }
      }
    }

    if (acquisition_thread_.joinable()) {
      acquisition_thread_.join();
    }
  }

  void acquisitionLoop()
  {
    try {
      auto hyperion = std::make_unique<Hyperion>(interrogator_ip_);

      {
        std::lock_guard<std::mutex> lock(hyperion_mutex_);
        active_hyperion_ = hyperion.get();
      }

      hyperion->enable_peak_streaming(stream_divider_);
      RCLCPP_INFO(
        get_logger(),
        "Connected to Hyperion at %s. Peak streaming enabled with stream_divider=%d",
        interrogator_ip_.c_str(),
        stream_divider_);

      while (!stop_requested_.load()) {
        hACQPeaks peaks = hyperion->stream_peaks();

        HyperionPeakSample sample;
        sample.serial = peaks.serialNumber;
        sample.instrument_timestamp = peaks.timeStamp;
        sample.wavelengths = peaks.get_all();
        sample.peak_counts.reserve(kHyperionChannelCount);

        for (uint16_t channel = 1; channel <= kHyperionChannelCount; ++channel) {
          sample.peak_counts.push_back(
            static_cast<uint32_t>(peaks.get_channel(channel).size()));
        }

        {
          std::lock_guard<std::mutex> lock(sample_mutex_);
          latest_sample_ = std::move(sample);
        }
      }

      try {
        hyperion->disable_peak_streaming();
      } catch (const std::exception & e) {
        if (!stop_requested_.load()) {
          RCLCPP_WARN(get_logger(), "Error disabling Hyperion peak streaming: %s", e.what());
        }
      }

      {
        std::lock_guard<std::mutex> lock(hyperion_mutex_);
        active_hyperion_ = nullptr;
      }
    } catch (const std::exception & e) {
      {
        std::lock_guard<std::mutex> lock(hyperion_mutex_);
        active_hyperion_ = nullptr;
      }

      if (!stop_requested_.load()) {
        RCLCPP_ERROR(get_logger(), "Hyperion acquisition thread lost connection: %s", e.what());
      }
    } catch (...) {
      {
        std::lock_guard<std::mutex> lock(hyperion_mutex_);
        active_hyperion_ = nullptr;
      }

      if (!stop_requested_.load()) {
        RCLCPP_ERROR(get_logger(), "Hyperion acquisition thread lost connection: unknown error");
      }
    }
  }

  void configurePublishTimer(double publish_rate_hz)
  {
    if (publish_timer_) {
      publish_timer_->cancel();
    }

    publish_timer_ = create_wall_timer(
      period_from_rate(publish_rate_hz),
      std::bind(&HyperionDriverNode::publishLatestSample, this));

    RCLCPP_INFO(get_logger(), "Publishing Hyperion peaks at %.3f Hz", publish_rate_hz);
  }

  void publishLatestSample()
  {
    std::optional<HyperionPeakSample> sample_copy;

    {
      std::lock_guard<std::mutex> lock(sample_mutex_);
      sample_copy = latest_sample_;
    }

    if (!sample_copy.has_value()) {
      RCLCPP_DEBUG_THROTTLE(
        get_logger(),
        *get_clock(),
        5000,
        "Waiting for first Hyperion sample before publishing");
      return;
    }

    hyperion_ros2_driver::msg::HyperionPeaks msg;
    msg.header.stamp = now();
    msg.header.frame_id = frame_id_;
    msg.serial = sample_copy->serial;
    msg.instrument_timestamp = sample_copy->instrument_timestamp;
    msg.peak_counts = sample_copy->peak_counts;
    msg.wavelengths = sample_copy->wavelengths;

    publisher_->publish(std::move(msg));
  }

  rcl_interfaces::msg::SetParametersResult onParametersChanged(
    const std::vector<rclcpp::Parameter> & parameters)
  {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;

    double requested_publish_rate = publish_rate_hz_;
    bool publish_rate_changed = false;

    for (const auto & parameter : parameters) {
      if (parameter.get_name() == "publish_rate_hz") {
        requested_publish_rate = parameter.as_double();
        publish_rate_changed = true;
        if (requested_publish_rate <= 0.0) {
          result.successful = false;
          result.reason = "publish_rate_hz must be greater than zero";
          return result;
        }
      }

      if (parameter.get_name() == "stream_divider") {
        const int requested_stream_divider = parameter.as_int();
        if (requested_stream_divider < 1) {
          result.successful = false;
          result.reason = "stream_divider must be greater than or equal to 1";
          return result;
        }
        if (requested_stream_divider != stream_divider_) {
          result.successful = false;
          result.reason = "stream_divider is only applied when the node starts";
          return result;
        }
      }
    }

    if (publish_rate_changed && requested_publish_rate != publish_rate_hz_) {
      publish_rate_hz_ = requested_publish_rate;
      configurePublishTimer(publish_rate_hz_);
    }

    return result;
  }

  std::string interrogator_ip_;
  double publish_rate_hz_ = 100.0;
  int stream_divider_ = 1;
  std::string frame_id_;

  std::atomic_bool stop_requested_{false};
  std::thread acquisition_thread_;

  std::mutex sample_mutex_;
  std::optional<HyperionPeakSample> latest_sample_;

  std::mutex hyperion_mutex_;
  Hyperion * active_hyperion_ = nullptr;

  rclcpp::Publisher<hyperion_ros2_driver::msg::HyperionPeaks>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr publish_timer_;
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr parameter_callback_handle_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<HyperionDriverNode>();
  rclcpp::spin(node);
  node.reset();

  rclcpp::shutdown();
  return 0;
}

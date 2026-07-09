
let isButtonActive = false;
let openButtonPressed = false; 


function togglecolor(button, command) {

    if(isButtonActive === true && openButtonPressed === false && command!=='allopen'){
        return;
    }

    button.style.backgroundColor = 'red';
    if (command === 'allopen') {
        const botoes = document.querySelectorAll('.button:not([onclick*="all"])');
        botoes.forEach(function(button) {
            button.style.backgroundColor = 'green';  // all buttons green
        });

        setTimeout(() => {
            button.style.backgroundColor = 'green'; // button open green
        },200); 
    }
}   


function showPoint(command) {

    if(isButtonActive === true && openButtonPressed === false && command!=='open'){
        return;
    }

    const pointsMap = {
        'thumb': 'point-thumb',
        'index': 'point-index',
        'middle': 'point-middle',
        'ring': 'point-ring',
        'pinky': 'point-pinky',
        'tripod': ['point-thumb', 'point-index', 'point-middle'],
        'pince': ['point-thumb', 'point-index'], 
        'four': ['point-index', 'point-middle', 'point-ring', 'point-pinky'],
        'powergrip': ['point-thumb', 'point-index', 'point-middle', 'point-ring', 'point-pinky']
    };

    // Check if the command refers to multiple points
    if (Array.isArray(pointsMap[command])) {
        // Show each point associated with the command
        pointsMap[command].forEach(idPonto => {
            const elementPoint = document.getElementById(idPonto);
            if (elementPoint) {
                elementPoint.style.display = 'block';
            }
        });
    } else {

        const elementPoint = document.getElementById(pointsMap[command]);
        if (elementPoint) {
            elementPoint.style.display = 'block';
        }
    }

    if(command==='open'){
        const points = document.querySelectorAll('.point');
        points.forEach(function(point) {
            point.style.display = 'none';  // Hiding all points
        });
    }

    if(command==='open2'){
        const points = document.querySelectorAll('.point');
        points.forEach(function(point) {
            point.style.display = 'none';  // Hiding all points
        });
    }
}

function sendCommand(command) {


    if(command==='open'){
    isButtonActive = false; 
    openButtonPressed = true; 
    }

    if(command==='open2'){
    isButtonActive = false; 
    openButtonPressed = true; 
    }

    if(isButtonActive === true && openButtonPressed === false){
        alert("Pressione o botão 'Abrir' para continuar.");
        return;
    }

    fetch(`/${command}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command }),
    })
    .then(response => {
        if (response.ok) {
            return response.json(); 
        } else {
            throw new Error('Error sending command');
        }
    })
    .then(data => {
        console.log('Server response:', data);
    })
    .catch(error => {
        console.error('Request error:', error);
    });
    
    if(command==='open'){
        return;
    }

    if(command==='open2'){
        return;
    }

    isButtonActive = true;
    openButtonPressed = false; 
}






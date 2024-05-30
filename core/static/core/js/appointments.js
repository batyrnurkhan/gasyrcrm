window.onload = function() {
    fetchAppointments();
};

function fetchAppointments() {
    fetch('http://127.0.0.1:8000/appointments/api/appointments/')
        .then(response => response.json())
        .then(data => {
            const appointmentsDiv = document.getElementById('appointments');
            appointmentsDiv.innerHTML = ''; // Clear current appointments
            data.forEach(appointment => {
                appointmentsDiv.innerHTML += `
                    <div>
                        <p>Date: ${appointment.date}</p>
                        <p>Time: ${appointment.start_time} to ${appointment.end_time}</p>
                        <button onclick="setLink('${appointment.id}')">Set Link</button>
                    </div>
                `;
            });
        }).catch(error => console.log('Error loading appointments:', error));
}

function openCreateModal() {
    document.getElementById('createModal').style.display = 'block';
}

function createAppointment(event) {
    event.preventDefault();
    const formData = new FormData(document.getElementById('createAppointmentForm'));
    fetch('/api/appointments/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            fetchAppointments(); // Reload appointments if successfully created
            document.getElementById('createModal').style.display = 'none';
        } else {
            alert('Failed to create appointment: ' + data.error);
        }
    });
}

function setLink(appointmentId) {
    const link = prompt('Please enter the meeting link:');
    if (link) {
        fetch(`/api/appointments/${appointmentId}/set_link/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ link: link })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                alert('Link set successfully');
            } else {
                alert('Failed to set link: ' + data.error);
            }
        });
    }
}

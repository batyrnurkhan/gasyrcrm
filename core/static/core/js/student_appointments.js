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
                if (!appointment.is_booked) {
                    appointmentsDiv.innerHTML += `
                        <div>
                            <p>Date: ${appointment.date}</p>
                            <p>Time: ${appointment.start_time} - ${appointment.end_time}</p>
                            <button onclick="bookAppointment('${appointment.id}')">Book Appointment</button>
                        </div>
                    `;
                }
            });
        });
}

function bookAppointment(appointmentId) {
    fetch(`/appointments/${appointmentId}/book_appointment/`, {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            alert('Appointment booked successfully');
            fetchAppointments(); // Reload appointments
        } else {
            alert('Failed to book appointment');
        }
    });
}

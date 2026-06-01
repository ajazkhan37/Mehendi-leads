document.addEventListener('DOMContentLoaded', function () {
    setupBookingForm();
    setupWhatsAppButton();
});

function setupBookingForm() {
    const form = document.getElementById('booking-form');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        if (!validateForm()) return;

        const getValue = (id) => {
            const el = document.getElementById(id);
            return el ? el.value : '';
        };

        const formData = {
            name: getValue('name'),
            phone: getValue('phone'),
            email: getValue('email'),
            event_date: getValue('event_date'),
            location: getValue('location'),
            budget: getValue('budget'), // may not exist in premium page; backend stores empty string fine
            additional_notes: getValue('additional_notes'),

            // production fields (backend supports these)
            pincode: getValue('pincode'),
            whatsapp_number: getValue('whatsapp_number'),
            full_address: getValue('full_address'),
            event_type: getValue('event_type'),
            lead_status: 'New',
            maps_link: getValue('maps_link')
        };

        fetch('/submit-booking', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccess();
                    form.reset();
                } else {
                    showError(data.message || 'Error submitting booking');
                }
            })
            .catch(err => {
                showError('Failed to submit booking: ' + err);
            });
    });
}

function validateForm() {
    const nameEl = document.getElementById('name');
    const phoneEl = document.getElementById('phone');

    if (!nameEl || !phoneEl) return false;

    const name = (nameEl.value || '').trim();
    const phone = (phoneEl.value || '').trim();

    const emailEl = document.getElementById('email');
    const email = emailEl ? (emailEl.value || '').trim() : '';

    const pincodeEl = document.getElementById('pincode');
    const whatsappEl = document.getElementById('whatsapp_number');
    const fullAddressEl = document.getElementById('full_address');

    const pincode = pincodeEl ? (pincodeEl.value || '').trim() : '';
    const whatsappNumber = whatsappEl ? (whatsappEl.value || '').trim() : '';
    const fullAddress = fullAddressEl ? (fullAddressEl.value || '').trim() : '';

    if (!name) {
        showError('Please enter your name');
        return false;
    }

    if (!phone) {
        showError('Please enter your phone number');
        return false;
    }

    if (!/^\d{10}$/.test(phone.replace(/\D/g, ''))) {
        showError('Please enter a valid 10-digit phone number');
        return false;
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showError('Please enter a valid email address');
        return false;
    }

    if (pincode && !/^\d{6}$/.test(pincode)) {
        showError('Please enter a valid 6-digit pincode');
        return false;
    }

    if (whatsappNumber) {
        const digits = whatsappNumber.replace(/\D/g, '');
        if (!/^\d{10}$/.test(digits) && !/^\d{12,15}$/.test(digits)) {
            showError('Please enter a valid WhatsApp number');
            return false;
        }
    }

    if (fullAddress && fullAddress.length < 5) {
        showError('Please enter a valid full address');
        return false;
    }

    // event_type might be required in premium UI; validate if present
    const eventTypeEl = document.getElementById('event_type');
    if (eventTypeEl) {
        if (!eventTypeEl.value) {
            showError('Please select an occasion');
            return false;
        }
    }

    return true;
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.display = 'block';
    errorDiv.textContent = message;

    const form = document.getElementById('booking-form');
    if (form) {
        form.insertBefore(errorDiv, form.firstChild);
        setTimeout(() => errorDiv.remove(), 4500);
    } else {
        alert(message);
    }
}

function showSuccess() {
    // old index version used #success-modal; premium page may not.
    const modal = document.getElementById('success-modal');
    if (modal) {
        modal.style.display = 'block';
        return;
    }

    const form = document.getElementById('booking-form');
    if (!form) return;

    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.display = 'block';
    successDiv.textContent = '✅ Booking submitted successfully! We’ll contact you soon.';

    form.insertBefore(successDiv, form.firstChild);
    setTimeout(() => successDiv.remove(), 5000);
}

function setupWhatsAppButton() {
    // premium page has #whatsapp-btn already
    const whatsappBtn = document.getElementById('whatsapp-btn');
    if (!whatsappBtn) return;

    whatsappBtn.addEventListener('click', function () {
        const phoneNumber =
            (window.MEHENDI_WHATSAPP_NUMBER || whatsappBtn.getAttribute('data-phone')) || '919876543210';

        const message = encodeURIComponent('Hi! I am interested in booking your mehendi services. Please contact me.');
        window.open(`https://wa.me/${phoneNumber}?text=${message}`, '_blank');
    });
}

// keep legacy close behavior safe (if modal exists)
window.onclick = function (event) {
    const modal = document.getElementById('success-modal');
    if (modal && event.target === modal) {
        modal.style.display = 'none';
    }
};

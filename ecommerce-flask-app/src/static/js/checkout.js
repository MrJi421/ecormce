// document.addEventListener('DOMContentLoaded', function() {
//     const checkoutForm = document.getElementById('checkoutForm');
//     if (!checkoutForm) return;

//     // Format card number input
//     const cardInput = document.getElementById('card_number');
//     cardInput.addEventListener('input', function(e) {
//         let value = e.target.value.replace(/\D/g, '');
//         if (value.length > 16) value = value.slice(0, 16);
//         e.target.value = value.replace(/(\d{4})/g, '$1 ').trim();
//     });

//     // Format expiry date input
//     const expiryInput = document.getElementById('expiry');
//     expiryInput.addEventListener('input', function(e) {
//         let value = e.target.value.replace(/\D/g, '');
//         if (value.length > 4) value = value.slice(0, 4);
//         if (value.length >= 2) {
//             value = value.slice(0, 2) + '/' + value.slice(2);
//         }
//         e.target.value = value;
//     });

//     // Format CVV input
//     const cvvInput = document.getElementById('cvv');
//     cvvInput.addEventListener('input', function(e) {
//         let value = e.target.value.replace(/\D/g, '');
//         if (value.length > 4) value = value.slice(0, 4);
//         e.target.value = value;
//     });

//     // Form validation
//     checkoutForm.addEventListener('submit', function(e) {
//         e.preventDefault();

//         if (validateForm()) {
//             this.submit();
//         }
//     });

//     function validateForm() {
//         const cardNumber = cardInput.value.replace(/\s/g, '');
//         const expiry = expiryInput.value;
//         const cvv = cvvInput.value;

//         if (cardNumber.length !== 16) {
//             alert('Please enter a valid 16-digit card number');
//             return false;
//         }

//         const [month, year] = expiry.split('/');
//         if (!month || !year || month > 12 || month < 1) {
//             alert('Please enter a valid expiry date (MM/YY)');
//             return false;
//         }

//         if (cvv.length < 3) {
//             alert('Please enter a valid CVV');
//             return false;
//         }

//         return true;
//     }
// });

function updateTotal() {
    const selectedOption = document.querySelector('input[name="shipping_method"]:checked');
    const shippingCost = parseFloat(selectedOption.value.split(':')[1]);
    const subtotal = { total };
    const total = subtotal + shippingCost;

    document.getElementById('shipping-cost').textContent = `$${shippingCost.toFixed(2)}`;
    document.getElementById('total-amount').textContent = `$${total.toFixed(2)}`;
}

document.getElementById('checkoutForm').addEventListener('submit', function(e) {
    const requiredFields = ['fullname', 'address', 'city', 'state', 'zipcode'];
    let isValid = true;

    requiredFields.forEach(field => {
        const input = document.getElementById(field);
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('error');
        } else {
            input.classList.remove('error');
        }
    });

    if (!isValid) {
        e.preventDefault();
        alert('Please fill in all required fields');
    }
});
// /*By Bukreedan Humaa Id:2412290*/
//Javascript for the review form :
// // Wait for the page to fully load before running the script
// document.addEventListener('DOMContentLoaded', function () {

//     // Grab all the elements we need from the page
//     const starContainer = document.getElementById('starRating');
//     const ratingInput = document.getElementById('ratingValue');
//     const form = document.getElementById('reviewForm');

//     // If any of these don't exist, just stop here
//     if (!starContainer || !ratingInput || !form) return;

//     // Get all the individual star elements
//     const stars = starContainer.querySelectorAll('span');
//     stars.forEach(s => s.style.cursor = 'pointer');

//     // This function colors the stars based on rating
//     function paintStars(value, activeColor = 'gold', inactiveColor = '#ccc') {
//         stars.forEach(s => {
//             const v = s.getAttribute('data-value');
//             // If star value is less than or equal to rating, color it gold
//             s.style.color = (Number(v) <= Number(value)) ? activeColor : inactiveColor;
//         });
//     }

//     // When user clicks on a star
//     starContainer.addEventListener('click', function (e) {
//         const target = e.target.closest('span');
//         if (!target) return;
//         // Save the rating value and update the stars
//         ratingInput.value = target.getAttribute('data-value');
//         paintStars(ratingInput.value);
//     });

//     // Show preview when hovering over stars
//     starContainer.addEventListener('mouseover', function (e) {
//         const target = e.target.closest('span');
//         if (!target) return;
//         paintStars(target.getAttribute('data-value'), '#ffd700');
//     });

//     // Reset to actual rating when mouse leaves
//     starContainer.addEventListener('mouseout', function () {
//         paintStars(ratingInput.value);
//     });

//     // Creates the success modal popup
//     function createModal() {
//         const overlay = document.createElement('div');
//         overlay.id = 'reviewModalOverlay';
//         overlay.className = 'review-modal-overlay';

//         const modal = document.createElement('div');
//         modal.className = 'review-modal';

//         const title = document.createElement('div');
//         title.textContent = '127.0.0.1:8000 says';
//         title.className = 'review-modal-title';

//         const message = document.createElement('div');
//         message.textContent = 'Your review has been submitted successfully!   Thank you for your feedback!';
//         message.className = 'review-modal-message';

//         const buttonContainer = document.createElement('div');
//         buttonContainer.className = 'review-modal-button-container';

//         const okButton = document.createElement('button');
//         okButton.textContent = 'OK';
//         okButton.className = 'review-modal-button';
        
//         // When OK button is clicked, close modal and submit form
//         okButton.addEventListener('click', function() {
//             overlay.remove();
//             form.submit(); // Actually submit the form to Django
//         });

//         // Put all the pieces together
//         buttonContainer.appendChild(okButton);
//         modal.appendChild(title);
//         modal.appendChild(message);
//         modal.appendChild(buttonContainer);
//         overlay.appendChild(modal);

//         return overlay;

//     }

//     // Handle form submission
//     form.addEventListener('submit', function (e) {
//         // Make sure user selected a rating first
//         if (!ratingInput.value || ratingInput.value === "0") {
//             e.preventDefault();
//             alert("Please select a star for your review.");
//             return;
//         }

//         e.preventDefault(); // Stop the form from submitting immediately
        
//         // Show the success modal instead
//         const modal = createModal();
//         document.body.appendChild(modal);
//     });

//     // Color the stars based on initial value (if any)
//     paintStars(ratingInput.value);
// });


/*By Bukreedan Humaa Id:2412290*/
//Jquery version of the above code for the review form :
// Wait for the page to fully load before running the script

$(document).ready(function () {

    
    // Grab all the elements we need from the page
    var $starContainer = $('#starRating');
    var $ratingInput   = $('#ratingValue');
    var $form          = $('#reviewForm');

    // If any of these don't exist, just stop here
    if (!$starContainer.length || !$ratingInput.length || !$form.length) return;

    // Make stars look clickable
    $starContainer.find('span').css('cursor', 'pointer');

    // This function colors the stars based on rating
    function paintStars(value, activeColor, inactiveColor) {
        activeColor   = activeColor   || 'gold';
        inactiveColor = inactiveColor || '#ccc';
        $starContainer.find('span').each(function () {
            var v = $(this).attr('data-value');
            $(this).css('color', (Number(v) <= Number(value)) ? activeColor : inactiveColor);
        });
    }

    // When user clicks on a star
    $starContainer.on('click', 'span', function () {
        // Save the rating value and update the stars
        $ratingInput.val($(this).attr('data-value'));
        paintStars($ratingInput.val());
    });

    // Show preview when hovering over stars
    $starContainer.on('mouseover', 'span', function () {
        paintStars($(this).attr('data-value'), '#ffd700');
    });

    // Reset to actual rating when mouse leaves
    $starContainer.on('mouseout', function () {
        paintStars($ratingInput.val());
    });

    // Creates the success modal popup
    function createModal() {
        var $overlay = $('<div>').attr('id', 'reviewModalOverlay').addClass('review-modal-overlay');
        var $modal   = $('<div>').addClass('review-modal');
        var $title   = $('<div>').addClass('review-modal-title').text('127.0.0.1:8000 says');
        var $message = $('<div>').addClass('review-modal-message').text('Your review has been submitted successfully!   Thank you for your feedback!');
        var $btnWrap = $('<div>').addClass('review-modal-button-container');
        var $okBtn   = $('<button>').addClass('review-modal-button').text('OK');

        // When OK is clicked — send data via AJAX then close modal
        $okBtn.on('click', function () {
            $.ajax({
                url:  $form.attr('action'),
                type: 'POST',
                data: $form.serialize(),
                success: function () {
                    $overlay.remove();
                    $form[0].reset();
                    paintStars(0);
                    $ratingInput.val('0');
                },
                error: function () {
                    $overlay.remove();
                    alert('Submission failed. Please try again.');
                }
            });
        });

        $btnWrap.append($okBtn);
        $modal.append($title, $message, $btnWrap);
        $overlay.append($modal);
        return $overlay;
    }

    // Handle form submission
    $form.on('submit', function (e) {
        e.preventDefault();

        // Make sure user selected a rating first
        if (!$ratingInput.val() || $ratingInput.val() === '0') {
            alert('Please select a star for your review.');
            return;
        }

        // Show the success modal — AJAX fires when user clicks OK inside it
        $('body').append(createModal());
    });

    // Color the stars based on initial value (if any)
    paintStars($ratingInput.val());

});



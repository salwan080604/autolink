// /*By Bukreedan Humaa Id:2412290*/
//these were the javascripts for the report form  :

// // Wait for everything to load before we start
// document.addEventListener("DOMContentLoaded", function () {
//     const form = document.getElementById("reportForm");

//     // Listen for when the form gets submitted
//     form.addEventListener("submit", function (event) {
//         event.preventDefault();  // Stop it from submitting right away

//         // Create the dark overlay background
//         const overlay = document.createElement('div');
//         overlay.className = 'report-modal-overlay';

//         // Create the main modal box
//         const modal = document.createElement('div');
//         modal.className = 'report-modal';

//         // Add the title text
//         const title = document.createElement('div');
//         title.textContent = '127.0.0.1:8000 says';
//         title.className = 'report-modal-title';

//         // Add the success message
//         const message = document.createElement('div');
//         message.textContent = 'Your report has been submitted successfully!';
//         message.className = 'report-modal-message';

//         // Create container for the OK button
//         const buttonContainer = document.createElement('div');
//         buttonContainer.className = 'report-modal-button-container';

//         // Create the OK button
//         const okButton = document.createElement('button');
//         okButton.textContent = 'OK';
//         okButton.className = 'report-modal-button';
        
//         // When they click OK, close the modal and submit the form
//         okButton.addEventListener('click', function() {
//             overlay.remove();
//             form.submit();  // Now actually submit to Django
//         });

//         // Put everything together
//         buttonContainer.appendChild(okButton);
//         modal.appendChild(title);
//         modal.appendChild(message);
//         modal.appendChild(buttonContainer);
//         overlay.appendChild(modal);
        
//         // Show it on the page
//         document.body.appendChild(overlay);
//     });
// });


// Wait for everything to load before we start
$(document).ready(function () {

    var $form = $('#reportForm');

    // Listen for when the form gets submitted
    $form.on('submit', function (e) {
        e.preventDefault(); // Stop it from submitting right away

        // Create the dark overlay background
        var $overlay = $('<div>').addClass('report-modal-overlay');
        var $modal   = $('<div>').addClass('report-modal');
        var $title   = $('<div>').addClass('report-modal-title').text('127.0.0.1:8000 says');
        var $message = $('<div>').addClass('report-modal-message').text('Your report has been submitted successfully!');
        var $btnWrap = $('<div>').addClass('report-modal-button-container');
        var $okBtn   = $('<button>').addClass('report-modal-button').text('OK');

        // When they click OK — send data via AJAX then close modal
        $okBtn.on('click', function () {
            $.ajax({
                url:  $form.attr('action'),
                type: 'POST',
                data: $form.serialize(),
                success: function () {
                    $overlay.remove();
                    $form[0].reset();
                },
                error: function () {
                    $overlay.remove();
                    alert('Submission failed. Please try again.');
                }
            });
        });

        // Put everything together
        $btnWrap.append($okBtn);
        $modal.append($title, $message, $btnWrap);
        $overlay.append($modal);

        // Show it on the page
        $('body').append($overlay);
    });

    
});
// Main/static/main.js
// ─────────────────────────────────────────────────────────────
// CONVERTED FROM PLAIN JS TO JQUERY
// Changes:
//   1. document.addEventListener('DOMContentLoaded') 
//      → $(document).ready() / $(function())
//   2. document.querySelectorAll() → $()
//   3. element.addEventListener() → .on() / .click()
//   4. Contact form → AJAX submission (no page reload)
//   5. Live vehicle search → AJAX $.ajax() call
// ─────────────────────────────────────────────────────────────

// ── CSRF SETUP (required for all POST AJAX requests) ─────────
// Must be set before any AJAX POST call
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (settings.type === 'POST') {
            xhr.setRequestHeader(
                'X-CSRFToken',
                $('[name=csrfmiddlewaretoken]').val()
            );
        }
    }
});


// ── CATEGORY CHART ───────────────────────────────────────────
function initCategoryChart() {
    var categoryData = {
        labels: [],
        counts: [],
        colors:      ['#1e3a8a','#0f766e','#d97706','#dc2626','#7c3aed','#0891b2'],
        hoverColors: ['#1e40af','#115e59','#b45309','#b91c1c','#6d28d9','#0e7490']
    };

    // jQuery selector instead of document.querySelectorAll
    $('.category-card').each(function() {
        var name  = $(this).find('h3').text();
        var count = parseInt($(this).find('.category-count').text()) || 0;
        categoryData.labels.push(name);
        categoryData.counts.push(count);
    });

    var ctx          = document.getElementById('categoryChart').getContext('2d');
    var totalVehicles = parseInt($('.chart-total').text()) || 0;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categoryData.labels,
            datasets: [{
                data:                 categoryData.counts,
                backgroundColor:      categoryData.colors,
                hoverBackgroundColor: categoryData.hoverColors,
                borderWidth:          2,
                borderColor:          '#ffffff',
                hoverBorderWidth:     3
            }]
        },
        options: {
            responsive:          true,
            maintainAspectRatio: true,
            cutout:              '65%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            var label      = context.label || '';
                            var value      = context.raw  || 0;
                            var percentage = totalVehicles > 0
                                ? ((value / totalVehicles) * 100).toFixed(1)
                                : 0;
                            return label + ': ' + value + ' vehicles (' + percentage + '%)';
                        }
                    },
                    backgroundColor: '#1e3a8a',
                    titleColor:      '#ffffff',
                    bodyColor:       '#ffffff',
                    borderColor:     '#d97706',
                    borderWidth:     1
                }
            },
            animation: {
                animateScale:  true,
                animateRotate: true,
                duration:      2000,
                easing:        'easeOutQuart'
            }
        }
    });
}


// ── TESTIMONIALS CAROUSEL ────────────────────────────────────
function initTestimonialsCarousel() {
    var $track  = $('#testimonialsTrack');
    var $cards  = $('.testimonial-card');
    var $dots   = $('#carouselDots');

    if (!$cards.length || $cards.length <= 3) {
        $('.prev-btn, .next-btn').hide();
        $dots.hide();
        return;
    }

    var currentIndex   = 0;
    var CARDS_PER_SLIDE = 3;
    var totalSlides    = Math.ceil($cards.length / CARDS_PER_SLIDE);

    // Build dots using jQuery .append()
    $dots.empty();
    for (var i = 0; i < totalSlides; i++) {
        (function(idx) {
            var $dot = $('<button>')
                .addClass('carousel-dot' + (idx === 0 ? ' active' : ''))
                .attr('aria-label', 'Go to slide ' + (idx + 1))
                .html('•')
                .on('click', function() { goToSlide(idx); });
            $dots.append($dot);
        })(i);
    }

    function updateCarousel() {
        var cardWidth  = $cards.first().outerWidth();
        var gap        = 32;
        var slideWidth = (cardWidth + gap) * CARDS_PER_SLIDE;
        var translateX = -currentIndex * slideWidth;

        $track.css({
            transform:  'translateX(' + translateX + 'px)',
            transition: 'transform 0.5s ease-in-out'
        });

        // Update dots using jQuery .toggleClass()
        $('.carousel-dot').each(function(i) {
            $(this).toggleClass('active', i === currentIndex);
        });

        // Update buttons
        $('.prev-btn').prop('disabled', currentIndex === 0)
                      .css('opacity', currentIndex === 0 ? '0.5' : '1');
        $('.next-btn').prop('disabled', currentIndex >= totalSlides - 1)
                      .css('opacity', currentIndex >= totalSlides - 1 ? '0.5' : '1');
    }

    function goToSlide(index) {
        if (index < 0 || index >= totalSlides) return;
        currentIndex = index;
        updateCarousel();
    }

    // jQuery .click() instead of addEventListener
    $('.prev-btn').click(function() {
        if (currentIndex > 0) { currentIndex--; updateCarousel(); }
    });

    $('.next-btn').click(function() {
        if (currentIndex < totalSlides - 1) { currentIndex++; updateCarousel(); }
    });

    // Touch support
    var startX = 0;
    $track.on('touchstart', function(e) {
        startX = e.originalEvent.touches[0].clientX;
        $track.css('transition', 'none');
    });
    $track.on('touchend', function(e) {
        var endX = e.originalEvent.changedTouches[0].clientX;
        var diff = startX - endX;
        $track.css('transition', 'transform 0.5s ease-in-out');
        if (Math.abs(diff) > 50) {
            if (diff > 0) { if (currentIndex < totalSlides - 1) { currentIndex++; } }
            else          { if (currentIndex > 0)               { currentIndex--; } }
        }
        updateCarousel();
    });

    // Window resize
    var resizeTimer;
    $(window).on('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(updateCarousel, 250);
    });

    updateCarousel();
}


// ── LIVE VEHICLE SEARCH (AJAX) ───────────────────────────────
// Fetches vehicles from /main/ajax/search/?q=... as user types
// Displays results below the search box without page reload
// This demonstrates: $.ajax(), success callback, JSON consumption
function initLiveSearch() {
    var $input    = $('#hero-search-input');
    var $results  = $('#hero-search-results');
    var searchTimer;

    if (!$input.length) return;

    $input.on('input', function() {
        var query = $(this).val().trim();
        clearTimeout(searchTimer);

        if (query.length < 2) {
            $results.hide().empty();
            return;
        }

        // Show loading indicator
        $results.show().html(
            '<div class="search-loading"><i class="fas fa-spinner fa-spin"></i> Searching...</div>'
        );

        // Debounce — wait 350ms before sending request
        searchTimer = setTimeout(function() {
            $.ajax({
                url:     '/ajax/search/',   // Django JsonResponse endpoint
                type:    'GET',
                data:    { q: query },
                success: function(response) {
                    // JSON consumption — response.vehicles is the array
                    $results.empty();

                    if (!response.vehicles.length) {
                        $results.html(
                            '<div class="search-no-results">No vehicles found for "' + query + '"</div>'
                        );
                        return;
                    }

                    // Build result items from JSON data
                    $.each(response.vehicles, function(i, v) {
                        var price     = parseInt(v.price).toLocaleString();
                        var badge     = v.is_rental ? 'For Rent' : 'For Sale';
                        var badgeClass = v.is_rental ? 'badge-rent' : 'badge-sale';
                        var imgHtml   = v.image
                            ? '<img src="' + v.image + '" alt="' + v.make + '">'
                            : '<div class="search-no-img"><i class="fas fa-car"></i></div>';

                        var $item = $(
                            '<a href="/vehicles/detail/' + v.id + '/" class="search-result-item">' +
                                '<div class="search-result-img">' + imgHtml + '</div>' +
                                '<div class="search-result-info">' +
                                    '<div class="search-result-title">' + v.make + ' ' + v.model + ' (' + v.year + ')</div>' +
                                    '<div class="search-result-meta">' + v.type + ' &bull; ' + v.fuel + '</div>' +
                                    '<div class="search-result-price">Rs ' + price +
                                        '<span class="search-badge ' + badgeClass + '">' + badge + '</span>' +
                                    '</div>' +
                                '</div>' +
                            '</a>'
                        );
                        $results.append($item);
                    });

                    // Add View JSON link + see all results
                    $results.append(
                        '<div class="search-footer">' +
                            '<a href="/ajax/search/?q=' + encodeURIComponent(query) +
                            '" target="_blank" class="search-view-json">' +
                            '<i class="fas fa-code"></i> View JSON</a>' +
                            '<a href="/vehicles/standardsearch/?search=' + encodeURIComponent(query) +
                            '" class="search-see-all">See all results <i class="fas fa-arrow-right"></i></a>' +
                        '</div>'
                    );
                },
                error: function() {
                    $results.html('<div class="search-no-results">Something went wrong. Try again.</div>');
                }
            });
        }, 350);
    });

    // Close results when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.hero-search-wrap').length) {
            $results.hide();
        }
    });

    // Show results again when focusing on input
    $input.on('focus', function() {
        if ($results.children().length) $results.show();
    });
}


// ── CONTACT FORM — AJAX SUBMISSION ───────────────────────────
// e.preventDefault() stops normal page reload
// $.ajax POST sends form data and shows response without reload
// This demonstrates: form.submit(), e.preventDefault(), $.ajax POST
function initContactForm() {
    $('.contact-form').on('submit', function(e) {
        e.preventDefault();  // MANDATORY — stops page reload (Agenda 13)

        var $form   = $(this);
        var $btn    = $form.find('.contact-submit-btn');
        var $msg    = $('#contact-ajax-message');

        // Disable button while submitting
        $btn.prop('disabled', true).html(
            '<i class="fas fa-spinner fa-spin"></i> Sending...'
        );

        // .serialize() converts all form fields to query string
        // and automatically includes CSRF token
        $.ajax({
            url:     '/ajax/contact/',
            type:    'POST',
            data:    $form.serialize(),
            success: function(response) {
                if (response.success) {
                    // Show success message dynamically — no page reload
                    $msg.removeClass('contact-error')
                        .addClass('contact-success')
                        .html('<i class="fas fa-check-circle"></i> ' + response.message)
                        .fadeIn(400);

                    $form[0].reset();  // Clear form fields

                    // Hide message after 5 seconds
                    setTimeout(function() { $msg.fadeOut(400); }, 5000);
                }
            },
            error: function(xhr) {
                var response = xhr.responseJSON;
                var errorMsg = 'Please fix the errors below.';

                if (response && response.errors) {
                    // Display field errors returned from Django
                    errorMsg = Object.values(response.errors).join(' ');
                }

                $msg.removeClass('contact-success')
                    .addClass('contact-error')
                    .html('<i class="fas fa-exclamation-circle"></i> ' + errorMsg)
                    .fadeIn(400);
            },
            complete: function() {
                // Re-enable button regardless of success/error
                $btn.prop('disabled', false).html(
                    'Send Message <i class="fas fa-paper-plane"></i>'
                );
            }
        });
    });
}


// ── $(document).ready() ──────────────────────────────────────
// jQuery equivalent of DOMContentLoaded
// Ensures all elements exist before running code
$(function() {
    if ($('#categoryChart').length) {
        initCategoryChart();
    }
    initTestimonialsCarousel();
    initLiveSearch();
    initContactForm();
    initLoginPrompt();
});

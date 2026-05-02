// CONVERTED FROM PLAIN JS TO JQUERY
// Changes:
//   1. document.addEventListener('DOMContentLoaded') 
//      → $(document).ready() / $(function())
//   2. document.querySelectorAll() → $()
//   3. element.addEventListener() → .on() / .click()
//   4. Contact form → AJAX submission (no page reload)
//   5. Live vehicle search → AJAX $.ajax() call
//   6. Homepage Stats & Featured Vehicles → REST API consumption
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

// ── LIVE STATS via REST API → updates donut chart center ─────
// Instead of a separate banner, the REST API stats are used to
// refresh the donut chart's center total and enrich the tooltip.
// Demonstrates: REST API consumption, JSON parsing, live DOM update.
function loadStats() {
    $.ajax({
        url:      '/api/homepage/stats/',
        type:     'GET',
        dataType: 'json',
        success: function(data) {
            console.log('✅ Stats loaded via REST API:', data);

            // JSON CONSUMPTION — update the donut chart center live
            // data.total_available is the real-time count from the API
            $('#chart-live-total').text(data.total_available);

            // Also store the by_type breakdown so the chart tooltip can use it
            // This enriches the existing Chart.js donut with live API data
            window._liveStats = data.by_type;
        },
        error: function(xhr, status, error) {
            console.error('❌ Error loading stats from REST API:', error);
            // Silently fail — the chart already shows the server-rendered total
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

                   // Store query for JSON shortcut
                    window._lastSearchQuery = query;

                    // Add see all results link
                    $results.append(
                        '<a href="/vehicles/standardsearch/?search=' + encodeURIComponent(query) +
                        '" class="search-see-all">See all results <i class="fas fa-arrow-right"></i></a>'
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
// FormData is used instead of .serialize() so that file attachments
// are correctly included in the POST request.
// This demonstrates: form.submit(), e.preventDefault(), $.ajax POST,
// JSON consumption of the server response, and FormData for file uploads.
function initContactForm() {
    $('.contact-form').on('submit', function(e) {
        e.preventDefault();  // MANDATORY — stops normal page reload

        var $form       = $(this);
        var $btn        = $form.find('.contact-submit-btn');
        var $msg        = $('#contact-ajax-message');
        var $jsonBox    = $('#contact-json-output');
        var $jsonPre    = $('#contact-json-pre');
        var $jsonStatus = $('#contact-json-status');

        $btn.prop('disabled', true).html(
            '<i class="fas fa-spinner fa-spin"></i> Sending...'
        );

        // FormData captures file inputs too — .serialize() would drop them
        var formData = new FormData($form[0]);

        $.ajax({
            url:         '/ajax/contact/',
            type:        'POST',
            data:        formData,
            processData: false,   // do NOT convert FormData to query string
            contentType: false,   // let the browser set multipart boundary
            success: function(response) {
                // JSON CONSUMPTION — response is a parsed JS object from Django
                if (response.success) {
                    $msg.removeClass('contact-error')
                        .addClass('contact-success')
                        .html('<i class="fas fa-check-circle"></i> ' + response.message)
                        .fadeIn(400);
                    $form[0].reset();
                    setTimeout(function() { $msg.fadeOut(400); }, 5000);
                }
                // Show raw JSON response below the form
                $jsonStatus.css({background:'#166534', color:'#bbf7d0'}).text('200 OK');
                $jsonPre.text(JSON.stringify(response, null, 2));
                $jsonBox.slideDown(300);
            },
            error: function(xhr) {
                // JSON CONSUMPTION — read error object returned by Django
                var response = xhr.responseJSON;
                var errorMsg = 'Please fix the errors below.';
                if (response && response.errors) {
                    errorMsg = Object.values(response.errors).join(' ');
                } else if (response && response.message) {
                    errorMsg = response.message;
                }
                $msg.removeClass('contact-success')
                    .addClass('contact-error')
                    .html('<i class="fas fa-exclamation-circle"></i> ' + errorMsg)
                    .fadeIn(400);
                // Show raw error JSON
                $jsonStatus.css({background:'#991b1b', color:'#fecaca'}).text(xhr.status + ' Error');
                $jsonPre.text(JSON.stringify(response || {error: 'Unknown error'}, null, 2));
                $jsonBox.slideDown(300);
            },
            complete: function() {
                $btn.prop('disabled', false).html(
                    'Send Message <i class="fas fa-paper-plane"></i>'
                );
            }
        });
    });
}


// ── LOGIN PROMPT (placeholder) ────────────────────────────────
function initLoginPrompt() {}

// ── PATCH / DELETE DEMO ───────────────────────────────────────
// Demonstrates authentication-restricted REST endpoints.
// PATCH marks a ContactMessage as resolved (admin only).
// DELETE removes a ContactMessage (admin only).
function initPatchDelete() {

    function showResult(statusCode, data, method) {
        var $out    = $('#patch-delete-output');
        var $status = $('#patch-delete-status');
        var $pre    = $('#patch-delete-pre');

        var isOk = statusCode < 400;
        $status.css({
            background: isOk ? '#166534' : '#991b1b',
            color:      isOk ? '#bbf7d0' : '#fecaca',
        }).text(statusCode + ' ' + (isOk ? '✅' : '❌'));

        $pre.text(
            '// ' + method + ' /api/contact/<id>/\n\n' +
            JSON.stringify(data, null, 2)
        );
        $out.slideDown(300);
    }

    // ── PATCH — mark message as resolved ────────────────────
    $('#patch-btn').on('click', function() {
        var id = $('#patch-delete-id').val().trim();
        if (!id) { alert('Enter a message ID first.'); return; }

        $.ajax({
            url:         '/api/contact/' + id + '/',
            type:        'PATCH',
            contentType: 'application/json',
            // JSON body — tells Django to set is_resolved = true
            data:        JSON.stringify({ is_resolved: true }),
            success: function(response) {
                showResult(200, response, 'PATCH');
            },
            error: function(xhr) {
                // 403 = not admin, 404 = wrong ID
                showResult(xhr.status, xhr.responseJSON || {}, 'PATCH');
            }
        });
    });

    // ── DELETE — remove a message entirely ──────────────────
    $('#delete-btn').on('click', function() {
        var id = $('#patch-delete-id').val().trim();
        if (!id) { alert('Enter a message ID first.'); return; }

        if (!confirm('Delete message #' + id + '? This cannot be undone.')) return;

        $.ajax({
            url:  '/api/contact/' + id + '/',
            type: 'DELETE',
            success: function(response) {
                showResult(204, response || { message: 'Deleted successfully.' }, 'DELETE');
            },
            error: function(xhr) {
                showResult(xhr.status, xhr.responseJSON || {}, 'DELETE');
            }
        });
    });
}


// ── $(document).ready() ──────────────────────────────────────
$(function() {
    if ($('#categoryChart').length) {
        initCategoryChart();
        loadStats();   // REST API call — updates chart center total live
    }
    initTestimonialsCarousel();
    initLiveSearch();
    initContactForm();
    initLoginPrompt();
    initPatchDelete();
});

// Script to get current year for footer
let currentYear = new Date().getFullYear();
document.querySelector('.footer').innerHTML = `&copy; ${currentYear} Your Company Name. <a href="your-link-here">Link to Page</a>`;

        $('#createBucketBtn').on('click', function() {
            let appName = $('#appNameInput').val().trim();
            let bucketName = $('#bucketNameInput').val().trim();
            if (!appName) {
                alert("Please enter an app name!");
                return;
            }
            if (!bucketName) {
                alert("Please enter a bucket name!");
                return;
            }
            $.ajax({
                url: "/create_bucket/",
                type: "POST",
                data: JSON.stringify({ app_name: appName, bucket: bucketName }),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(data) {
                    if (data.message) {
                        alert("Bucket '" + bucketName + "' under App '" + appName + "' created successfully! An email has been sent to the owner if configured.");
                        location.reload();
                    } else {
                        alert("Error creating bucket: " + data.error);
                    }
                },
                error: function(xhr, status, error) {
                    alert("An error occurred: " + xhr.responseText);
                }
            });
        });

    // ToggleTheme Functions
    $(document).ready(function(){
    // Check local storage for theme
    if (localStorage.getItem('theme') === 'dark') {
        $('body').attr('data-theme', 'dark');
        $('.sun-icon').hide();
        $('.moon-icon').show();
    }

    // Toggle theme on SVG icon click
    $('#themeToggleIcon').on('click', function() {
        if ($('body').attr('data-theme') === 'dark') {
            $('body').removeAttr('data-theme');
            localStorage.setItem('theme', 'light');
            $('.sun-icon').show();
            $('.moon-icon').hide();
        } else {
            $('body').attr('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            $('.sun-icon').hide();
            $('.moon-icon').show();
        }
    });
});

    // Search Functions

$(document).ready(function() {
    $("#searchInput").on("keyup", function() {
        const value = $(this).val().toLowerCase();

        // If the search bar is empty, collapse all
        if (!value) {
            $(".collapse").collapse('hide');
            return;
        }

        $("table tbody tr").each(function() {
            const row = $(this);
            if (row.text().toLowerCase().indexOf(value) > -1) {
                row.show();
                row.closest('.collapse').collapse('show');  // Expand the parent collapsible
            } else {
                row.hide();
            }
        });
    });
});

$('#resendBucketDetailsBtn').on('click', function() {
    let appName = $('#appNameInput').val().trim();
    let bucketName = $('#bucketNameInput').val().trim();
    if (!appName) {
        alert("Please enter an app name!");
        return;
    }
    if (!bucketName) {
        alert("Please enter a bucket name!");
        return;
    }
    $.ajax({
        url: "/resend_bucket_details",  // This should be the endpoint for resending bucket details
        type: "POST",
        data: JSON.stringify({ app_name: appName, bucket: bucketName }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(data) {
            if (data.message) {
                alert(data.message);
                location.reload();
            } else {
                alert("Error resending bucket details: " + data.error);
            }
        },
        error: function(xhr, status, error) {
            alert("An error occurred: " + xhr.responseText);
        }
    });
});

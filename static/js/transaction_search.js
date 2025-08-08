$(document).ready(function() {
    // Add X button next to search bar
    $('#transaction-search').parent().append('<i id="clear-search" class="material-icons" style="cursor: pointer; position: absolute; right: 10px; top: 50%; transform: translateY(-50%); display: none;">clear</i>');
    
    // Store original page title and HTML
    var originalTitle = $('#page-title').text();
    var originalHtml = null;

    $('#transaction-search').on('input', function() {
        // Show/hide X button based on if there's text
        $('#clear-search').toggle(!!$(this).val());
    });

    // Clear search and restore original page
    $('#clear-search').click(function() {
        $('#transaction-search').val('');
        $(this).hide();
        if (originalHtml) {
            $('#transactions-bin').replaceWith(originalHtml);
            if ($("#transactions-scroller").length !== 0) { 
                new SimpleBar($("#transactions-scroller")[0]);
            }
            $('#page-title').text(originalTitle);
        }
    });

    $('#transaction-search').keypress(function(e) {
        if (e.which == 13) { // Enter key
            e.preventDefault();
            var searchTerm = $(this).val().trim();
            if (!searchTerm) return;
            
            // Store original HTML before first search
            if (!originalHtml) {
                originalHtml = $('#transactions-bin').clone();
            }
            
            $.ajax({
                url: '/api/search-transactions',
                type: 'POST',
                data: {
                    'search_term': searchTerm,
                    'page': 1,
                    'csrf_token': $('#csrf-token').val()
                },
                beforeSend: function() {
                    Budgeteer.loadingSpinner.show();
                },
                success: function(response) {
                    if (response.error) {
                        M.toast({html: response.error});
                        return;
                    }
                    $('#transactions-bin').replaceWith(response.html);
                    if ($("#transactions-scroller").length !== 0) { 
                        new SimpleBar($("#transactions-scroller")[0]);
                    }
                    updateLoadMoreButton(response.has_more);
                    // Update page title
                    if (response.page_title) {
                        $('#page-title').text(response.page_title);
                    }
                },
                complete: function() {
                    Budgeteer.loadingSpinner.hide();
                }
            });
        }
    });
});

function updateLoadMoreButton(hasMore) {
    if (hasMore) {
        if ($('#load-more').length === 0) {
            $('#bin').append('<div class="center-align"><a id="load-more" class="btn waves-effect waves-light">Load More</a></div>');
        }
    } else {
        $('#load-more').remove();
    }
}

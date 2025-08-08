window.Budgeteer = window.Budgeteer || {};
Budgeteer.previous_page = null; // Used to store the previous page before a search
Budgeteer.only_clear_searchfield = true; // If true, only clear the search field, if false, return to previous page after search

$(document).ready(function() {


    $('#transaction-search').on('input', function() {
        // Show/hide the #close-search icon based on if there's text
        $('#close-search').toggle(!!$(this).val());
    });

    // Clear search and restore original page using the existing #close-search
    $('#close-search').click(function() {
        $(this).hide();
        if (Budgeteer.only_clear_searchfield) {
            $('#transaction-search').val('');
            return;
        } else {
            $('#transaction-search').val('');
            console.log("Previous page: " + Budgeteer.previous_page)
            $.ajax({
                type: 'POST',
                url: '/api/reset-search',
                data: JSON.stringify({"previous_page": Budgeteer.previous_page, "timestamp": gen_timestamp()}),
                contentType: 'application/json'
            }).done(function(o) {
                if (o['error']) { M.toast({html: o['error']}); return; }
                $('#transactions-bin').replaceWith(o['transactions_html']);
                if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]) } //Re-initialize the transactions-scroller if the envelope has transactions
                $('#current-view').text(o['current_view']);
                $("#separator").show();
                $('#page-total').text(o['page_total']).show();
                refresh_reconcile();
            });
        }
    });

    $('#transaction-search').keypress(function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            Budgeteer.only_clear_searchfield = false;
            var searchTerm = $(this).val().trim();
            if (!searchTerm) return;
            $("#multi-select-icons").addClass("hide");
            Budgeteer.previous_page = Budgeteer.current_page;
            Budgeteer.current_page = "Search Results";
            $.ajax({
                type: 'POST',
                url: '/api/search-transactions',
                data: JSON.stringify({'search_term': searchTerm, "timestamp": gen_timestamp()}),
                contentType: 'application/json'
            }).done(function(o) {
                if (o.error) {M.toast({html: o.error}); return;}
                $('#transactions-bin').replaceWith(o.transactions_html);
                if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]); }
                $('#current-view').text(o.current_page);
                $("#page-total").hide();
                $("#separator").hide();
            });
        }
    });

});

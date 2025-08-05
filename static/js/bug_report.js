// Handles the bug report from submission on the error page and the main page within the bug report modal.
$("#bug-report-modal").modal();

$('#bug-report-form').submit(function(e) {
    e.preventDefault();
    var url = $(this).attr('action');
    var method = $(this).attr('method');
    var $form = $(this);
    var $parentModal = $("#bug-report-modal");
    var formData = new FormData(this);
    formData.append('timestamp', gen_timestamp());
    $.ajax({
    type: method,
    url: url,
    cache: false,
    contentType: false,
    processData: false,
    data: formData
    }).done(function( o ) {
    if (o.success) {
        $parentModal.modal("close");
        $form[0].reset(); //Clears the data from the form fields
    } else {
        if (o.errors) {
        displayFieldErrors(o.errors);
        }
    }
    if (o['toasts']) {  //Display toasts
        o['toasts'].forEach((toast) => M.toast({html: toast}));
    }
    });
});

$('#screenshot_filepath').change(function() {
    $(this).siblings(".helper-text").text("");
});
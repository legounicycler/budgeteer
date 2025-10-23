class FormSelectWithIcon extends M.FormSelect {
  _setValueToInput() {
    var values = [];
    var options = this.$el.find('option');

    options.each(function (el) {
      if ($(el).prop('selected')) {
        // Clone the option to avoid modifying original DOM
        let $clone = $(el).clone();

        // Remove only <i class="material-icons"> elements
        $clone.find('i.material-icons').remove();

        // Get cleaned text
        let text = $clone.text().trim();

        // Add the text to the input
        values.push(text);
      }
    });

    if (!values.length) {
      var firstDisabled = this.$el.find('option:disabled').eq(0);
      if (firstDisabled.length && firstDisabled[0].value === '') {
        let $clone = firstDisabled.clone();
        $clone.find('i.material-icons').remove();
        let text = $clone.text().trim();
        values.push(text);
      }
    }

    this.input.value = values.join(', ');
  }
}

// Register it to the Materialize namespace
M.FormSelectWithIcon = FormSelectWithIcon;


// Create a jQuery wrapper similar to Materialize's pattern
if (window.jQuery) {
  (function ($) {
    $.fn.formSelectWithIcon = function (options) {
      this.each(function () {
        if (!$(this).hasClass('browser-default')) {
          M.FormSelectWithIcon.init(this, options);
        }
      });
      return this;
    };
  })(jQuery);
}
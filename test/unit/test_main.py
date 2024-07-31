import pytest

# When testing the envelope/account transfer creation, test for what happens if the user submits invalid form data with BOTH
# accounts and envelopes selected. This would only happen on programatic data submissions. The frontend behavior adds/removes
# the required attribute to the select fields when the user toggles the transfer type.
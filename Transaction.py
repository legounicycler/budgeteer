class Transaction:

    def __init__(self, type, name, amt, date, envelope, account, grouping, note):
        self.id = None
        self.type = type
        self.name = name
        self.amt = amt
        self.date = date
        self.envelope = envelope
        self.account = account
        self.grouping = grouping
        self.note = note

        def get_id():
            return self.id

        def set_id(id):
            self.id = id

        def get_type():
            return self.type

        def set_type(type):
            self.type = type

        def get_name():
            return self.name

        def set_name(name):
            self.name = name

        def get_amt():
            return self.amt

        def set_amt(amt):
            self.amt = amt

        def get_date():
            return self.date

        def set_date(date):
            self.date = date

        def get_envelope():
            return self.envelope

        def set_envelope(envelope):
            self.envelope = envelope

        def get_acount():
            return self.account

        def set_account(account)
            self.account = account

        def get_grouping():
            return self.grouping

        def set_grouping(grouping):
            self.grouping = grouping

        def get_note():
            return self.note

        def set_note(note):
            self.note = note
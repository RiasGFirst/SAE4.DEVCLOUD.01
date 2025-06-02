from tortoise import fields, Model


class Account(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)


class Balance(Model):
    id = fields.IntField(primary_key=True)
    account = fields.ForeignKeyField("models.Account", related_name="balances")
    amount = fields.DecimalField(max_digits=10, decimal_places=2)


class Beneficiary(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    account = fields.ForeignKeyField("models.Account", related_name="beneficiaries")


class Transaction(Model):
    id = fields.IntField(primary_key=True)
    account = fields.ForeignKeyField("models.Account", related_name="transactions")
    beneficiary = fields.ForeignKeyField("models.Beneficiary", related_name="transactions")
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    date = fields.DatetimeField(auto_now_add=True)
    description = fields.CharField(max_length=255, null=True)

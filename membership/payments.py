"""Provider boundary: future webhooks must verify signatures before entering this layer."""
from .security import Problem, clean


class ManualPayments:
    name = 'manual'

    def confirm(self, db, application_id, actor, data, settings, timestamp):
        if settings.fee_minor is None:
            raise Problem('Configurer LNH_FEE_MINOR et LNH_CURRENCY avant toute confirmation de paiement.', 409)
        amount = data.get('amount_minor')
        if type(amount) is not int or amount != settings.fee_minor or data.get('currency') != settings.currency:
            raise Problem('Le montant ou la devise ne correspond pas au droit configuré.')
        reference = clean(data.get('reference'), 'référence du paiement', 160)
        db.execute('INSERT INTO payments VALUES(?,?,?,?,?,?,?)',
                   (application_id, self.name, amount, settings.currency, reference, timestamp, actor))

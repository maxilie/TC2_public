from tc2.account.AlpacaAccount import AlpacaAccount
from tc2.health_checking.health_check.AbstractHealthCheck import AbstractHealthCheck
from tc2.health_checking.HealthCheckResult import HealthCheckResult


class AlpacaCheck(AbstractHealthCheck):
    """
    Not meant to be accessed except by HealthChecker.
    Checks that Alpaca accepts our API credentials.

    Conditions for success:
    + Account query does not return 'invalid credentials'.
    """

    def run(self, acct: AlpacaAccount) -> HealthCheckResult:
        try:
            acct_info = acct.rest_client.get_account()
            self.debug('Acct info: {}'.format(acct_info))

            orders = acct.rest_client.list_orders(status='all')
            self.debug('Order history: {}'.format(orders))
            # Pass the model_type if conditions are met
            self.set_passing(True)
            if len(str(acct_info)) < 124:
                self.debug('Acct info response seems too short to be valid. Check the logs!')
                self.set_passing(False)
        except Exception as e:
            self.debug('Error fetching credentials: {}'.format(e.args))
            self.set_passing(False)

        return self.make_result()

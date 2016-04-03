from processors.githubnotifications.github_notification_processor import GithubNotificationProcessor
from processors.stackexchange.stack_exchange_notification_processor import StackExchangeNotificationProcessor

from metastore import MetaStore
from processors.charges.charge_card_processor import ChargeCardProcessor


def add_processors(processors):
    processors.append(StackExchangeNotificationProcessor(MetaStore("stack_exchange_1"), "My SO filters"))
    processors.append(ChargeCardProcessor(MetaStore("charge_cards"))
                      .with_amex()
                      .with_chase()
                      .with_barclaycard()
#                      .with_bofa()
                      .with_citi())
    processors.append(GithubNotificationProcessor(MetaStore("github_notifications")))

from abc import ABCMeta, abstractmethod


class BaseNotificationDigester:
    __metaclass__ = ABCMeta

    @abstractmethod
    def process_new_notification(self, rfc822content, msg, html_message, text_message):
        """
        Process new email notification
        :rtype: True or False based on whether the email was processed or not
        """
        pass

    @abstractmethod
    def rewrite_rollup_emails(self, rollup_inbox_proxy, has_previous_message, previously_seen, sender_to_implicate):
        """
        Rewrite (or write, or don't at all) the rollup email, in the rollup email account
        :param sender_to_implicate: The From message is set to this "Firstname Secondname" <email@addr>
        :param previously_seen: True if the current rollup email has been read
        :param has_previous_message:  True is there is a current rollup for this at all (could have been deleted)
        :param rollup_inbox_proxy:  Use this to orchestrate delete and actual rewrite
        """
        pass

    @abstractmethod
    def matching_incoming_headers(self):
        """
        :rtype: List of headers that would mean a match, like: ["From: alerts@example.com"]
        """
        pass

    @abstractmethod
    def matching_rollup_subject(self):
        """
        :rtype: Subject that we're matching on, like "Foobar Rollup"
        """
        pass

    @abstractmethod
    def print_summary(self):
        """
        :rtype: print a summary (or not) at the end
        """
        pass

import random
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from tc2.account.data_stream.StreamUpdate import StreamUpdate
from tc2.account.data_stream.StreamUpdateType import StreamUpdateType


class StreamUpdateQueue:
    """
    An update queue for storing data + account updates during their transfer
        between processes.
    """

    # The longest number of seconds to keep an update for
    UPDATE_STORE_DURATION = 8

    # Unprocessed updates in this queue
    updates: List[StreamUpdate] = []
    # Updates already processed
    updates_seen: List[StreamUpdate] = []

    def get_next_update(self,
                        master_queue: List[StreamUpdate],
                        moment: datetime,
                        strategy_start: datetime,
                        symbols: Optional[List[str]] = None) -> Optional[StreamUpdate]:
        """
        Returns the next unseen stream update, if there is one, and marks it as seen.
        :param master_queue: the list of recent updates:
            For live trading, AccountDataStream.get_updates();
            For simulations, a list of simulated stream updates
        :param strategy_start: moment when strategy started
        """

        # When queue is empty, get unseen updates from the master list.
        if len(self.updates) == 0:
            least_recent_update_time = moment - timedelta(seconds=self.UPDATE_STORE_DURATION)
            least_recent_update_time = max(least_recent_update_time, strategy_start)
            for update in master_queue:
                # Ignore master's updates for other symbols.
                if symbols is not None and update.get_symbol() is not None and update.get_symbol() not in symbols:
                    continue
                # Add master's updates that have yet to be processed.
                if update not in self.updates and update not in self.updates_seen \
                        and update.update_moment >= least_recent_update_time:
                    self.add_new_update(update)

            # Return None if there are no unseen updates in the queue or master.
            if len(self.updates) == 0:
                return None

        # Occasionally do pruning and sanity check.
        if random.randint(0, 100) < 5:
            # Warn if updates are accumulating (they might not be getting processed).
            if len(self.updates) > 3000:
                print(f'WARNING: Suspiciously high number of stream updates queued ({len(self.updates)})')

            # Trim updates_seen to 999.
            if len(self.updates_seen) > 999:
                self.updates_seen = self.updates_seen[:-999]

        # Show account updates before price updates.
        next_update_index = 0
        for i in range(len(self.updates)):
            if self.updates[i].update_type is StreamUpdateType.ORDER:
                next_update_index = i
                break
            elif self.updates[i].update_type is StreamUpdateType.ACCT_INFO \
                    and self.updates[next_update_index].update_type is not StreamUpdateType.ORDER:
                next_update_index = i

        # Remove and return the newest, highest-priority, unseen update.
        next_update = self.updates.pop(next_update_index)
        self.updates_seen.append(next_update)
        # print(f'Forwarding unseen update with id {next_update.update_id}')
        return next_update

    def add_new_update(self,
                       update: StreamUpdate) -> None:
        """
        Adds a new stream update to the queue and pushes out old updates.
        """

        # Add the update.
        self.updates.append(update)

        # Push out old updates.
        oldest_time_allowable = update.update_moment - timedelta(seconds=self.UPDATE_STORE_DURATION)
        self.updates = [old_update for old_update in self.updates if old_update.update_moment >= oldest_time_allowable]

    def to_json(self) -> Dict[str, any]:
        return {
            'updates':      [update.to_json() for update in self.updates],
            'updates_seen': [update.to_json() for update in self.updates]
        }

    @classmethod
    def from_json(self, json_data: Dict[str, any]) -> 'StreamUpdateQueue':
        try:
            queue = StreamUpdateQueue()
            queue.updates = [StreamUpdate.from_json(update_json) for update_json in json_data['updates']]
            queue.updates_seen = [StreamUpdate.from_json(update_json) for update_json in json_data['updates_seen']]
            return queue
        except Exception as e:
            traceback.print_exc()

import discordrpc

# Import timestamp function from discordrpc.utils to get current timestamp
from discordrpc.utils import timestamp


rpc = discordrpc.RPC(app_id=123456789)

rpc.set_activity(
      name="Timestamp Example",
      state="With timestamp!",
      details="Timestamp",
      ts_start=timestamp(), # Timestamp start
      ts_end=timestamp() + 3600 # Timestamp end (one hour from now)
    )



rpc.run()
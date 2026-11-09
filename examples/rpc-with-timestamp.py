import discordrpc

# Import timestamp variable from discordrpc.utils to get current timestamp
from discordrpc.utils import timestamp


rpc = discordrpc.RPC(app_id=123456789)

rpc.set_activity(
      name="Timestamp Example",
      state="With timestamp!",
      details="Timestamp",
      ts_start=timestamp(), # Timestamp start
      ts_end=1752426021 # Timestamp end
    )



rpc.run()
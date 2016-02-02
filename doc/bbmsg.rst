bbmsg - Playback of rosbag message from Bagbunker
=================================================

It is possible to play or fetch (partial) bag files directly from Bagbunker::

  % bbmsg play http://bb.instance/marv/api/messages/<md5>
  % bbmsg play http://bb.instance/marv/api/messages/<md5>?topic=/foo&topic=/bar
  % bbmsg play http://bb.instance/marv/api/messages/<md5>?topic=/foo&msg_type=std_msgs/String
  % bbmsg fetch-bag http://bb.instance/marv/api/messages/<md5>

  (topic1 OR topic2) AND (msg_type1 OR msg_type2)

Bagbunker needs to open the bag file for play. Over network this might be slow. If you want to use ``bbmsg`` it is recommended to have the bag files physically on the same machine as the one running Bagbunker.

For playback and saving bag files, all message types for the topics you are fetching need to be known on the client, i.e. the corresponding python packages need to be available.

For playback of messages, ``use_sim_time`` is set and the timestamps of the messages are published as ``/clock``.

WARNING: bbmsg is a young tool, keep a close eye on whether it works properly for your use cases.

BIGGER WARNING: bbmsg unpickles data received from the network and currently does not limit the classes allowed to be instatiated - you have to trust your network. This will be fixed in 3.1.0.

from pprint import pprint
from rocketchat_API.rocketchat import RocketChat


#rocket = RocketChat('teamplan', 'foo123', server_url='https://notify.certificateservices.se')
rocket = RocketChat('teamplan', 'foo123', server_url='http://localhost:3000')
pprint(rocket.me().json())
pprint(rocket.channels_list().json())
pprint(rocket.chat_post_message('Schema news, test 0001!', channel='GENERAL').json())
pprint(rocket.channels_history('GENERAL', count=5).json())

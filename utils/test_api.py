from pprint import pprint
from time import sleep

from pgoapi.utilities import get_cell_ids

from utils import setup_logging, setup_api

SERVICE_PROVIDER = "ptc"
USERNAME = "57b8927e60bd0"
PASSWORD = "57b8927e60bd0"

def main():
    setup_logging()

    position = (42.878529, -8.544476, 0)  # Catedral
    # api = setup_api(position, SERVICE_PROVIDER, USERNAME, PASSWORD)
    api = setup_api(position, "ptc", "3e46eyhgdeg34e", "3e46eyhgdeg34e")

    if api is None:
        return

    pprint(api.get_player())
    sleep(5)

    cell_ids = get_cell_ids(position[0], position[1])
    timestamps = [0, ] * len(cell_ids)
    response_dict = api.get_map_objects(latitude=position[0], longitude=position[1], since_timestamp_ms=timestamps,
                                        cell_id=cell_ids)
    pprint(response_dict)


    # sleep(5)
    # pprint(api.get_gym_details(gym_id="56aceecbfc7546199476b7324838ff2e.16"))

    # pprint(api.get_inventory())
    # pprint(api.get_player_profile())

    # pprint(api.fort_search(player_latitude=position[0], player_longitude=position[1]))

if __name__ == '__main__':
    main()

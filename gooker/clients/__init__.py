from gooker import base
from gooker.clients.ezlinks import LACityClient, LosRoblesClient, TeirraRejadaClient
from gooker.clients.foreup import WestchesterClient, RusticCanyonClient
from gooker.clients.letsgogolf import (
    LosVerdesClient,
    MountainMeadowsClient,
    ElDoradoClient,
    BrooksideKoinerClient,
    BrooksideNayClient,
)

clients: list[type[base.TeeTimeClient]] = [
    LACityClient,
    LosRoblesClient,
    WestchesterClient,
    RusticCanyonClient,
    TeirraRejadaClient,
    LosVerdesClient,
    MountainMeadowsClient,
    ElDoradoClient,
    BrooksideKoinerClient,
    BrooksideNayClient,
]

from gooker import base
from gooker.clients.ezlinks import LACityClient, LosRoblesClient, TeirraRejadaClient
from gooker.clients.foreup import (
    WestchesterClient,
    RusticCanyonClient,
    BethpageBlackClient,
    BethpageRedClient,
    BethpageBlueClient,
    BethpageGreenClient,
    BethpageYellowClient,
)
from gooker.clients.letsgogolf import (
    LosVerdesClient,
    MountainMeadowsClient,
    ElDoradoClient,
    BrooksideKoinerClient,
    BrooksideNayClient,
)
from gooker.clients.teeitup import IndustryHillsIkeClient, IndustryHillsBabeClient

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
    IndustryHillsIkeClient,
    IndustryHillsBabeClient,
    BethpageBlackClient,
    BethpageRedClient,
    BethpageBlueClient,
    BethpageGreenClient,
    BethpageYellowClient,
]

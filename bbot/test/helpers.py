import requests_mock
from abc import abstractmethod
from omegaconf import OmegaConf


class MockHelper:
    targets = ["blacklanternsecurity.com"]
    config_overrides = {}
    additional_modules = []

    def __init__(self, config, bbot_scanner, *args):
        self.name = self.__class__.__name__.lower()
        self.config = OmegaConf.merge(config, OmegaConf.create(self.config_overrides))
        self.scan = bbot_scanner(
            *self.targets, modules=[self.name] + self.additional_modules, name=f"{self.name}_test", config=self.config
        )
        self.scan.prep()
        self.module = self.scan.modules[self.name]

    def run(self):
        events = list(e for e in self.scan.start() if e.module == self.module)
        assert self.check_events(events)

    @abstractmethod
    def check_events(self, events):
        raise NotImplementedError


class RequestMockHelper(MockHelper):
    @abstractmethod
    def mock_args(self):
        raise NotImplementedError

    def register_uri(self, uri, method="GET", **kwargs):
        self.m.register_uri(method, uri, **kwargs)

    def run(self):
        with requests_mock.Mocker() as m:
            self.m = m
            self.mock_args()
            events = list(e for e in self.scan.start() if e.module == self.module)
            for x in events:
                print(x)
            assert self.check_events(events)


class HttpxMockHelper(MockHelper):

    targets = ["http://127.0.0.1:8888/"]

    def __init__(self, config, bbot_scanner, bbot_httpserver):
        self.bbot_httpserver = bbot_httpserver
        super().__init__(config, bbot_scanner)
        self.mock_args()

    @abstractmethod
    def mock_args(self):
        raise NotImplementedError

    def set_expect_requests(self, expect_args={}, respond_args={}):
        if "uri" not in expect_args:
            expect_args["uri"] = "/"
        self.bbot_httpserver.expect_request(**expect_args).respond_with_data(**respond_args)

from context import KLine, BackTestContext


class IStrategy(object):
    def __init__(self, context: BackTestContext):
        self.context = context

    def run(self, kline: KLine):
        pass

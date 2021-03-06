# -*- coding: utf-8 -*-
from datetime import timedelta

from openprocurement.auctions.tessel.models import TesselAuction
from openprocurement.auctions.core.adapters import (
    AuctionConfigurator,
    AuctionManagerAdapter
)
from openprocurement.auctions.core.plugins.awarding.v3_1.adapters import (
    AwardingV3_1ConfiguratorMixin
)
from openprocurement.auctions.core.utils import (
    calculate_business_date,
    SANDBOX_MODE,
    get_now,
    TZ,
)
from openprocurement.auctions.tessel.constants import (
    DUTCH_PERIOD,
    QUICK_DUTCH_PERIOD
)


class AuctionTesselConfigurator(AuctionConfigurator,
                                AwardingV3_1ConfiguratorMixin):
    name = 'Auction Tessel Configurator'
    model = TesselAuction


class AuctionTesselManagerAdapter(AuctionManagerAdapter):

    def create_auction(self, request):
        auction = request.validated['auction']
        if not auction.enquiryPeriod:
            auction.enquiryPeriod = type(auction).enquiryPeriod.model_class()
        if not auction.tenderPeriod:
            auction.tenderPeriod = type(auction).tenderPeriod.model_class()
        now = get_now()
        start_date = TZ.localize(auction.auctionPeriod.startDate.replace(tzinfo=None))
        auction.auctionPeriod.startDate = None
        auction.auctionPeriod.endDate = None
        auction.tenderPeriod.startDate = auction.enquiryPeriod.startDate = now
        pause_between_periods = start_date - (start_date.replace(hour=20, minute=0, second=0, microsecond=0) - timedelta(days=1))
        auction.enquiryPeriod.endDate = calculate_business_date(start_date, -pause_between_periods, auction).astimezone(TZ)
        time_before_tendering_end = (start_date.replace(hour=9, minute=30, second=0, microsecond=0) + DUTCH_PERIOD) - auction.enquiryPeriod.endDate
        auction.tenderPeriod.endDate = calculate_business_date(auction.enquiryPeriod.endDate, time_before_tendering_end, auction)
        if SANDBOX_MODE and auction.submissionMethodDetails and 'quick' in auction.submissionMethodDetails:
            auction.tenderPeriod.endDate = (auction.enquiryPeriod.endDate + QUICK_DUTCH_PERIOD).astimezone(TZ)
        auction.auctionPeriod.startDate = None
        auction.auctionPeriod.endDate = None
        auction.date = now
        if not auction.auctionParameters:
            auction.auctionParameters = type(auction).auctionParameters.model_class()

    def change_auction(self, request):
        pass

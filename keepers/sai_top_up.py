#!/usr/bin/env python3
#
# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse

import logging

from api import Address
from api.approval import directly
from api.numeric import Ray
from api.numeric import Wad
from keepers.sai import SaiKeeper


class SaiTopUp(SaiKeeper):
    def __init__(self):
        super().__init__()
        self.liquidation_ratio = self.tub.mat()
        self.minimum_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.minimum_margin)
        self.target_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.target_margin)

    def args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--minimum-margin", help="Margin between the liquidation ratio and the top-up threshold", type=float)
        parser.add_argument("--target-margin", help="Margin between the liquidation ratio and the top-up target", type=float)

    def startup(self):
        self.approve()
        self.on_block(self.check_all_cups)

    def approve(self):
        self.tub.approve(directly())

    def check_all_cups(self):
        for cup in self.our_cups():
            self.check_cup(cup)

    def check_cup(self, cup):
        top_up_amount = self.required_top_up(cup)
        if top_up_amount:
            if top_up_amount >= self.skr.balance_of(self.our_address):
                self.tub.lock(cup.cup_id, top_up_amount)
            else:
                logging.info(f"Cannot top-up as our balance is less than {top_up_amount} SKR.")

    def our_cups(self):
        for cup_id in range(1, self.tub.cupi()+1):
            cup = self.tub.cups(cup_id)
            if cup.lad == self.our_address:
                yield cup

    def required_top_up(self, cup):
        pro = cup.ink*self.tub.tag()
        tab = self.tub.tab(cup.cup_id)
        if tab > Wad(0):
            current_ratio = Ray(pro / tab)
            if current_ratio < self.minimum_ratio:
                return tab * (Wad(self.target_ratio - current_ratio) / self.tub.tag())
            else:
                return None
        else:
            return None


if __name__ == '__main__':
    SaiTopUp().start()
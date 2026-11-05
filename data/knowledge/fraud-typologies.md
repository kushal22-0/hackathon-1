# Fraud typologies for transaction monitoring

## Circular transfers

A circular transfer network moves value through a sequence of accounts and
returns it, partially or wholly, to the originating account. Rings can make
funds appear to have legitimate trading history, inflate balances, or obscure
the beneficial owner. Investigators should compare amounts after each hop,
look for fees skimmed at each step, and check whether the same device, IP, or
customer cluster controls multiple accounts in the ring.

Detection signals: directed cycles of length two or greater, repeated
counterparties, tight time spacing, round-number amounts, and shared identity
attributes across ring members.

## Fan-in

Fan-in occurs when many accounts send funds to a single destination, often a
mule or consolidation account. The destination may then forward a larger amount
to an external account or cash-out channel. Small individual transfers can stay
below reporting thresholds while the aggregate is significant.

Detection signals: high in-degree within a short window, sources with little
prior relationship to the destination, rapid consolidation, and onward wire
transfers.

## Fan-out

Fan-out is the mirror pattern: one source distributes funds to many destination
accounts in a short period. It is common in disbursement fraud, stolen-card
cash-out, and layering. The source may be a compromised account or a mule
funded by an earlier fan-in.

Detection signals: high out-degree, amounts below thresholds, repeated device
or IP usage across transactions, and destinations that immediately forward
funds.

## Rapid-fire transfers

A burst of transactions from one account, often small values, can indicate
account takeover, automated abuse, or structuring. The pattern is meaningful
when compared with the account's own baseline and with the number of distinct
counterparties.

## Large transfers

A single high-value transfer is not inherently fraud, but it warrants review
when it is unusual for the customer, uses an unfamiliar device or channel, or
is followed by rapid onward movement. Threshold-based rules must be tuned to
the institution and combined with contextual signals to control false
positives.

## Shared devices and IPs

Multiple accounts transacting from one device or IP can indicate a fraud ring,
a mule network, or a legitimate shared household. Identity links should be
treated as supporting evidence, not proof. The strength increases when the
accounts have no declared relationship, when sessions overlap, or when the
shared identity is also associated with rapid transfer patterns.

## Structuring and smurfing

Structuring deliberately keeps individual transactions under reporting or
monitoring thresholds while aggregating value across accounts or time. Look for
clusters just below threshold values, repeated amounts, and coordinated timing.

from . import (
    ats_greenhouse, ats_lever, ats_ashby, ats_smartrecruiters,
    ats_recruitee, ats_personio, ats_workday,
    agg_arbeitnow, agg_arbeitsagentur, agg_remotive, agg_remoteok, agg_himalayas,
)

# name -> callable(cfg: dict, companies: dict) -> list[Job]
REGISTRY = {
    "greenhouse": ats_greenhouse.fetch,
    "lever": ats_lever.fetch,
    "ashby": ats_ashby.fetch,
    "smartrecruiters": ats_smartrecruiters.fetch,
    "recruitee": ats_recruitee.fetch,
    "personio": ats_personio.fetch,
    "workday": ats_workday.fetch,
    "arbeitnow": agg_arbeitnow.fetch,
    "arbeitsagentur": agg_arbeitsagentur.fetch,
    "remotive": agg_remotive.fetch,
    "remoteok": agg_remoteok.fetch,
    "himalayas": agg_himalayas.fetch,
}

#!/usr/bin/env python

import click, opaque, sys, binascii

cfgmap = {
    'notPackaged': opaque.NotPackaged,
    'inSecEnv': opaque.InSecEnv,
    'inClrEnv': opaque.InClrEnv,
    'np': opaque.NotPackaged,
    'sec': opaque.InSecEnv,
    'clr': opaque.InClrEnv
}

cfgumap = {
    0: opaque.NotPackaged,
    1: opaque.InSecEnv,
    2: opaque.InClrEnv
}

def ascfg(c: int):
    cfg=opaque.PkgConfig()
    cfg.skU=cfgumap[c & 3]
    cfg.pkU=cfgumap[(c >> 2) & 3]
    cfg.pkS=cfgumap[(c >> 4) & 3]
    cfg.idU=cfgumap[(c >> 6) & 3]
    cfg.idS=cfgumap[(c >> 8) & 3]
    return cfg

@click.command()
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
@click.option('--cfg', required=True, type=int)
@click.option('--userid')
@click.option('--serverid' )
@click.option('--key')
@click.option('--sk')
@click.argument('record', type=click.File('wb'))
@click.argument('export_key', type=click.File('wb'))
def register(password, cfg, userid, serverid, key, sk, record, export_key):
    ids=opaque.Ids(userid, serverid)
    rec, ekey = opaque.Register(password, cfg, ids, key=None, sk=None)
    record.write(rec)
    export_key.write(ekey)

@click.command()
@click.option('--skU', type=click.Choice(['notPackaged', 'inSecEnv', 'np','sec'], case_sensitive=False))
@click.option('--pkU', type=click.Choice(cfgmap.keys(), case_sensitive=False))
@click.option('--pkS', type=click.Choice(cfgmap.keys(), case_sensitive=False))
@click.option('--idU', type=click.Choice(cfgmap.keys(), case_sensitive=False))
@click.option('--idS', type=click.Choice(cfgmap.keys(), case_sensitive=False))
def cfg(sku, pku, pks, idu, ids):
    r = ((cfgmap.get(sku,opaque.InSecEnv)) +
         (cfgmap.get(pku,opaque.InSecEnv) << 2) +
         (cfgmap.get(pks,opaque.InSecEnv) << 4) +
         (cfgmap.get(idu,opaque.InSecEnv) << 6) +
         (cfgmap.get(ids,opaque.InSecEnv) << 8)
    )
    print(r)

if __name__ == '__main__':
    if sys.argv[1] == 'cfg':
        del sys.argv[1]
        cfg()
    elif sys.argv[1] in ('reg', 'register'):
        del sys.argv[1]
        register()

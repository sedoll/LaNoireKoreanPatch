import struct
def parse(d):
    assert d[:4]==b'BMF\x03', d[:4]
    p=4; blocks={}
    while p<len(d):
        t=d[p]; sz,=struct.unpack_from('<I',d,p+1); blocks[t]=d[p+5:p+5+sz]; p+=5+sz
    info=blocks[1]; common=blocks[2]
    fs,bits,cs,sh,aa,pu,pr,pd,pl,sph,spv,ol=struct.unpack_from('<hBBHBBBBBBBB',info)
    name=info[14:].split(b'\0')[0].decode('latin1')
    lh,base,sw,shh,pages,bits2,a,r,g,b=struct.unpack_from('<HHHHHBBBBB',common)
    pagenames=[x.decode() for x in blocks[3].split(b'\0') if x]
    chars=[struct.unpack_from('<IHHHHhhhBB',blocks[4],i) for i in range(0,len(blocks[4]),20)]
    kern=[struct.unpack_from('<IIh',blocks.get(5,b''),i) for i in range(0,len(blocks.get(5,b'')),10)]
    return dict(size=fs,name=name,lineh=lh,base=base,w=sw,h=shh,pages=pages,pagenames=pagenames,chars=chars,kern=kern,blocks=blocks,info=struct.unpack_from('<hBBHBBBBBBBB',info),common=struct.unpack_from('<HHHHHBBBBB',common))

# none/hash/cdc/fastcdc.py
# ========================
#
# Copying
# -------
#
# Copyright (c) 2020 none authors and contributors.
#
# This file is part of the *none* project.
#
# None is a free software project. You can redistribute it and/or
# modify it following the terms of the MIT License.
#
# This software project is distributed *as is*, WITHOUT WARRANTY OF ANY
# KIND; including but not limited to the WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE and NONINFRINGEMENT.
#
# You should have received a copy of the MIT License along with
# *none*. If not, see <http://opensource.org/licenses/MIT>.
#
import typing as ty
import secrets

from none.collection.i import onexlast


# Source:
#    https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia


#: FastCDC minimum chunk size: 2KB.
GHASH_CHUNK_LO = (1 << 11) & 0xFFFFFFFFFFFFFFFF
#: FastCDC average chunk size: 8KB.
GHASH_CHUNK_MD = (1 << 13) & 0xFFFFFFFFFFFFFFFF
#: FastCDC maximum chunk size: 64KB.
GHASH_CHUNK_HI = (1 << 16) & 0xFFFFFFFFFFFFFFFF

#: FastCDC Gear hash low-end mask value, with 15 bits set to ``1``.
GHASH_MASK_LO = 0x0003590703530000
#: FastCDC Gear hash middle-end mask value, with 13 bits set to ``1``.
GHASH_MASK_MD = 0x0000D90303530000
#: FastCDC Gear hash high-end mask value, with 11 bits set to ``1``.
GHASH_MASK_HI = 0x0000D90003530000

#: A default gear table for developers in a hurry. This table is used by all the
#: FastCDC functions by default. It is however advised to create your own gear
#: table for your own use case.
# fmt: off
GHASH_TABLE = (
    0x75C11608EEE03D5A, 0x1DCBF468321B52F1, 0xE99851EBB44BB2EE, 0x5FA24004703795CF,
    0x2066258C9C3FAEFE, 0x464A08F43B3461D0, 0x3F4C68802E4E3118, 0x1EEC4ED078C29609,
    0xF4B95C2E08FF80C5, 0x2E50A50DAA60C85A, 0x6BC8784A264519FA, 0xFADB56DB30BE52C2,
    0xD0B958E1592BEF0C, 0x915C0E2E33AD7791, 0xFCEAF347A0613082, 0x0DA5D5F5D6D322AD,
    0xCC05C864BEC1CDBF, 0xA9716B7FDBEC0B68, 0x0796179CAB8B007F, 0x857AA8382C1EFDA3,
    0x121D984B1AA7F587, 0x9335E32D76DCA2E3, 0x6047DD259C30C795, 0x32946C9FF88B91C2,
    0xAEB9C467994D70E4, 0x17F2BCF9B9674FB2, 0x4D04231E912C7A7A, 0x5DBC6987F8A1C53E,
    0x9DAE3232D61345C5, 0x3344EF72DFF08B18, 0x781A70B8507EA08A, 0xC78C553778C38C2E,
    0x1F6B436E25A8C842, 0x487555F2C1EB66F4, 0x72033978B2921D9E, 0xABB4241AD70ADBAE,
    0x277039B31BEE3C62, 0x68F5DAB4A2DEF487, 0x724A779D673B0B79, 0x6475F7330A773B5E,
    0xA531195B9208AE0A, 0xF503E3E2D384D8B0, 0x8B6C4366A9CACEAE, 0xD88F0A2F4E35F716,
    0xC7F2B708F63B8A54, 0xE83E292B4B471D01, 0xA9AC0FAE75830A1C, 0x551076C09355E8A8,
    0x10CBCDDA98811A91, 0xA6D5666683FB5322, 0x09FDB4CB5DA36110, 0x57318DE6EAF4A119,
    0x424E2497B7629FED, 0xAD07686C0A950579, 0x3BA4E9B1F9E43FF1, 0xD99EA3C2DD76D62C,
    0x8852E1B8175D3B3E, 0xC990A3D9BCFDC890, 0xE8F282E468EB960A, 0xE2C444005B70E46E,
    0x36E5D505A7ACF315, 0xF51CBBD3B799C925, 0x2176A092DFDE9A10, 0xED99123273536201,
    0x2627C6C1965FDDFD, 0xE3A79EAE8FC0F025, 0x44657D9EEFBE9B34, 0xB141E46350961075,
    0x48D3AA86B91E88DD, 0x43B38F7E3396A758, 0x46E97C0E1BC80D6C, 0xA50160094DA0B237,
    0x2DD0667AA6A307CB, 0xCC520AF7DBE1B0B6, 0x5FDDD3042008EEAC, 0x27CE4578CCD9BEEA,
    0x39D8F596DB316BF8, 0xAB4E3D52FEB46F8A, 0xB12F0725E2F92DB5, 0x50303ADE2F26F423,
    0xE1FFFDAE8ACB28A3, 0xA3398970D9FBCAFA, 0x65E4183A6F813FB5, 0x904F60FD0274A2CB,
    0xD2FCA1B64EF9DF27, 0x9E78B3F7669D2428, 0x8D1E3CEABA38A9BB, 0x816FC527B575977F,
    0x21EC6863ED882E9E, 0xF68EBB3A4721DE2E, 0xA24A7C1B720BE7B2, 0x0267EB4579DDC184,
    0x0342A21D23CD8B53, 0xA13FB9E784532BAA, 0x1087439399A4B813, 0x323140606BC558D6,
    0xD0E44B67228F48AF, 0x514991A2CCBDB154, 0x6138361BB44DB33E, 0xE87EC1DC6F293B94,
    0x279A8935E7E752E4, 0x50E8008DFB85A55D, 0x657F4583571564BF, 0xAE7A60A573A42BAA,
    0x21BD3E898A7866BA, 0x5892088828F3C352, 0xE83299E0FA7397EA, 0x2EA73429C307F635,
    0xA0DAFD6E2D686715, 0xB3C577DE86E5B106, 0xC2438CD3A3BB28E3, 0xA14C0749AE5FA39A,
    0xAAF7BA9D3985430B, 0xC949924BADB239AC, 0xE4056A2A06AEF43D, 0xF3E36881BFFCB53C,
    0x663313A61B8B1D37, 0x6DFDAD5E5E5CB545, 0x300745F81CD413E2, 0xDBC2C79E6265FE2D,
    0xE7CBB80FD7DB3DC3, 0xA4407A130A0F472E, 0x4462501B764E889D, 0xE1F5D5B13118647B,
    0xC47C48313D424846, 0x4A62CB6B3BA95173, 0xB38472E8715FE2BE, 0x20B07584F71A7EA4,
    0x2C6FE6E72FBE272D, 0xD4499B8F9FC11BE2, 0x5904D2A0087B4BEF, 0xEB6411CF611D5582,
    0xFD3E98051DF49AA0, 0x78B4CE7A44069960, 0x26D4E7FED8D1F44D, 0x2DCBD263510D926C,
    0x57E352D2836E19BA, 0x1A949190D3A11848, 0x884A4A32FA4BF4D6, 0xCD6D78035F387C40,
    0xDE6372C0C7A8AD9B, 0x189C50D1B46A784C, 0x7787E0FDBF9EBFD6, 0x150F22D241D44444,
    0xBCD4A05697D767C1, 0x6753AC8963F6C8A7, 0x9F8052794EC0F50A, 0x944C4BD93ED52BF3,
    0xC6D3C33F3AD3E1F9, 0xF827608AA8DF8F63, 0xE29B6FB9F71CAA7F, 0x9037A065844637D6,
    0x67D2ED1A8C540CA5, 0xF2F0260EE1262616, 0x43F2635C3C7AE667, 0xE0FCB8AB1CA742E8,
    0xBE0058077E72EF25, 0xA6FDDC5061BB15C4, 0xF62B79C500171E60, 0x631186D977F9AF65,
    0xBA4F78A0B95CF69C, 0x3DF9EFF2557CE25D, 0xBC92FA5D5957F0D3, 0xE1B1D38519ABAA5A,
    0x393141B87550B599, 0x614AB400EF87F9E1, 0x0F85FCA53E93CF62, 0xC54FA9F8A55080F7,
    0xF591E6026FAD3026, 0x84CFA1C61EDED2B1, 0x7BEB727519F03080, 0x0BA60D2F18DF15C6,
    0xB1D96BCE591088AF, 0x956923A1DB27C414, 0x7D0E64F253B7D668, 0x6687D800E041047F,
    0x6A820E7020A70933, 0xC74DC8CDC2F332CF, 0x079B5E8C17ABF0B5, 0x2F22F24EC702DD36,
    0x1F70BFB77061EC15, 0xBD3412317A6D01DE, 0x1BF87A236104A4DC, 0xC0B49FA5A3DA2520,
    0x4DFF16DA7DA30DD4, 0xFED3CCE28332616E, 0x8F10CD6BCA254E06, 0xB481650D4816EA1A,
    0x8BDF211E1F8411DB, 0xECDDDA6D1463D09E, 0x7B177F67E35C84C2, 0x5A1AE03865EED703,
    0xCDE5A24092E10BD1, 0xCEB46EF4F9D82BF1, 0x5F28B0D97714C8A3, 0x666B724AFDBD4263,
    0x9ED8D7514040C0EE, 0x67F2A3E0EAE46744, 0xDCF6C3BB7F810322, 0x7A27904ABA691A45,
    0xC8A6FF887B7A5A6E, 0x916B51F8EC459F70, 0x1E97051E7D8C550B, 0x26BB8C4FD5564467,
    0xCB77D4A1C9F80BA2, 0xCCB853603F25D0FB, 0x4AE976D4023E1600, 0x7F329FF44E551001,
    0x97195897129C76E7, 0x2D470CB7FB6D6D68, 0xCA4B2D325E626D41, 0xFDCD3E975E60FAD1,
    0x2C89A85EBDB5994E, 0x40BF24C4A982D7AE, 0xD6EF185FC5A1D208, 0xF21647FEC1D34960,
    0xC0BE752934D02B10, 0x60366E088F909178, 0x362E6D73A4D1413B, 0xAD5AA36C2E9FD46B,
    0xF25B1BEED32195F4, 0x1C54B58AD6955D43, 0x3F2D5E4C86D5F51C, 0x6CD5565A29D56BF0,
    0xC11DA8C3DCDBEF9B, 0x46209271660D4DCD, 0x3C1733E06A83BAE9, 0x0620558584D9BD8C,
    0x10937CB289E45DC8, 0xA696CFC4CAB4F640, 0xE9C165DCBB98A95A, 0x8765FD6387954EB9,
    0xC1975907FEEE4885, 0xC8D71CA9F9F9BC18, 0xECDE21285EE40E12, 0x4FC006214423BE43,
    0x1DE581E005612EBA, 0x972D6FA7717F2A0E, 0x2616C9728AA620B3, 0x059240B1F454B2BD,
    0xB51FDA0DDCCC8A58, 0x76A01C3552E080EF, 0xFA1D3002D5F4CC71, 0x5850FCDA89DE6542,
    0xBF5FA6B1107F4F7D, 0x4ED9B22B64DF9C4E, 0xD9B840F489C8EE36, 0x8A0683D18834AB52,
    0x53A3FF2D6F9E9F68, 0x216578468E9BC74B, 0xC5541487D3AA5148, 0x1428606A9F57ADF9,
    0xC89104F2BBFDAD68, 0xECCFEFE44DC39D83, 0xACB944EEAFF632CE, 0xA3FA5D88F1BE735F,
)
# fmt: on


def mkgear() -> ty.Tuple[int, ...]:
    """Generate a tuple a 256 random integer value to be used as the Gear hash
    table.


    :returns: A tuple of 256 integer randomly generated.
    :rtype: ~typing.Tuple[int, ...]

    """
    # A gear hash table is composed of 256 random 64-bit (8-byte) integers.
    return tuple(secrets.randbits(64) & 0xFFFFFFFFFFFFFFFF for _ in range(256))


def ghash(
    h: int,
    ch: int,
    ghash_table: ty.Sequence[int] = GHASH_TABLE,
    seed: ty.Optional[int] = None,
) -> int:
    """Employs an array of 256 random integers to map with the numerical value
    of the given byte.


    :param h: The current gear hash value within a chunking process. When
              starting this value is usually initialized to ``0``.
    :type h: int

    :param ch: The integer value (``0`` - ``255``) of the character being added
               to the hash.
    :type ch: int

    :param ghash_table: A list of 256 integer values to map with the numerical
                        value of the character being added to the hash.
    :type ghash_table: ~typing.Sequence[int]

    :param seed: A 64-bit (8-byte) integer which is applied to the hash table
                 value for further randomization.
    :type seed: ~typing.Optional[int]


    :returns: A new Gear hash value including the provided character.
    :rtype: int

    """
    gear = ghash_table[ch] if seed is None else ghash_table[ch] ^ seed
    return ((h << 1) + gear) & 0xFFFFFFFFFFFFFFFF


def find(
    data: bytes,
    ghash_table: ty.Sequence[int] = GHASH_TABLE,
    seed: ty.Optional[int] = None,
) -> int:
    """Find the next cutting FastCDC point within given data.


    :param data: Data stream to cut.
    :type data: bytes

    :param ghash_table: A list of 256 integer values to map with the numerical
                        value of the character being added to the hash.
    :type ghash_table: ~typing.Sequence[int]

    :param seed: A 64-bit (8-byte) integer which is applied to the hash table
                 value for further randomization.
    :type seed: ~typing.Optional[int]


    :returns: Index value at which data must be cut.
    :rtype: int

    """
    h = 0  # Holder of the hash value.
    idx = GHASH_CHUNK_LO  # Set index to the minimum chunk size.

    # Mask selection sentinels.
    sentinel_md = GHASH_CHUNK_MD
    sentinel_hi = data_size = len(data)

    # If given data is lower than the minimum chunk size we return data length.
    if data_size <= GHASH_CHUNK_LO:
        return data_size

    # Evaluate appropriate sentinel value.
    if data_size >= GHASH_CHUNK_HI:
        sentinel_hi = GHASH_CHUNK_HI
    elif data_size <= GHASH_CHUNK_MD:
        sentinel_md = data_size

    for sentinel, mask in [
        (sentinel_md, GHASH_MASK_LO),
        (sentinel_hi, GHASH_MASK_HI),
    ]:
        while idx < sentinel:
            h = ghash(h, data[idx], ghash_table=ghash_table, seed=seed)
            if not h & mask:
                return idx
            idx += 1

    return idx


def split(
    data, ghash_table: ty.Sequence[int] = GHASH_TABLE, seed: ty.Optional[int] = None
) -> ty.Generator[ty.Tuple[int, int, bytes], None, None]:
    """Split given data stream in normalized FastCDC chunks.


    :param data: Data stream to be divided.
    :type data: bytes

    :param ghash_table: A list of 256 integer values to map with the numerical
                        value of the character being added to the hash.
    :type ghash_table: ~typing.Sequence[int]

    :param seed: A 64-bit (8-byte) integer which is applied to the hash table
                 value for further randomization.
    :type seed: ~typing.Optional[int]


    :returns: A three items tuple with the chunk start index, the chunk length
              and the chunk data.
    :rtype: ~typing.Generator[~typing.Tuple[int, int, bytes], None, None]

    """
    data_size = len(data)  # Maximum length of the data.
    ck_start = 0  # Chunk start index within the data.
    ck_end = 0  # Chunk end index within the data.
    ct_idx = GHASH_CHUNK_HI  # Current cutting index.

    while ct_idx != ck_end:
        ck_end = ck_start + find(
            data[ck_start:ct_idx], ghash_table=ghash_table, seed=seed
        )

        yield ck_start, ck_end, data[ck_start:ck_end]
        ck_start, ct_idx = ck_end, min(ck_end + GHASH_CHUNK_HI, data_size)


def fastcdc(
    stream: ty.BinaryIO,
    ghash_table: ty.Sequence[int] = GHASH_TABLE,
    seed: ty.Optional[int] = None,
) -> ty.Generator[ty.Tuple[int, int, bytes], None, None]:
    """Read given binary stream and split it in normalized chunks using the
    `Fast and Efficient Content-Defined Chunking (FastCDC)
    <https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia>`_
    approach.


    :param stream: A pointer to the binary stream of the data to be chunked.
    :type stream: ~io.RawIOBase

    :param ghash_table: A list of 256 integer values to map with the numerical
                        value of the character being added to the hash.
    :type ghash_table: ~typing.Sequence[int]

    :param seed: A 64-bit (8-byte) integer which is applied to the hash table
                 value for further randomization.
    :type seed: ~typing.Optional[int]


    :returns: A three items tuple with the chunk start index, the chunk length
              and the chunk data.
    :rtype: ~typing.Generator[~typing.Tuple[int, int, bytes], None, None]

    """
    st_idx = 0  # Current position in the binary stream.
    remain = bytearray()  # Data remaining from the chunking process.
    buffer = bytearray(GHASH_CHUNK_HI)  # Buffer to keep file data.

    while True:
        # Load up to :data:`~none.hash.cdc.fastcdc.GHASH_CHUNK_HI` file data
        # into the buffer.
        read_bytes = stream.readinto(buffer)
        if read_bytes == 0:
            # No more data? We're getting out of here.
            break

        # We prepend remaining data from previous iteration before chopping.
        buffer = remain + buffer
        # Keep in mind read data can be lower than actual buffer size.
        bf_end = read_bytes + len(remain)

        # :func:`~none.hash.cdc.fastcdc.split` will cut all provided data,
        # however the last chunk may not be the end of the file and we may still
        # have some more data to read.
        #
        # Therefore, we keep the last chunk aside looking for a potential
        # bigger chunk.
        ck_idx = 0
        for ck_start, ck_end, ck_data in onexlast(
            split(buffer[:bf_end], ghash_table=ghash_table, seed=seed)
        ):
            yield st_idx + ck_start, st_idx + ck_end, bytes(ck_data)
            ck_idx = ck_end

        # Saving the last chunk of data for the next iteration.
        remain = buffer[ck_idx:bf_end]
        buffer = bytearray(GHASH_CHUNK_HI - len(remain))

        # Raising our file index.
        st_idx += ck_idx

    # We're done reading the file, chopping remaining data.
    if remain:
        for ck_start, ck_end, ck_data in split(
            remain, ghash_table=ghash_table, seed=seed
        ):
            yield st_idx + ck_start, st_idx + ck_end, bytes(ck_data)

import typing
import asyncio

L = typing.TypeVar('L')


def chunks(lst: typing.Iterator[L], n: int):
    rr = []
    for item in lst:
        rr.append(item)
        if len(rr) == n:
            yield rr
            rr = []
    yield rr


async def async_chunks(lst: typing.AsyncGenerator[L, None], n: int):
    rr = []
    async for item in lst:
        rr.append(item)
        if len(rr) == n:
            yield rr
            rr = []
    yield rr


T = typing.TypeVar('T')
S = typing.TypeVar('S')


async def run_in_parallel(action: typing.Callable[[T], S], instances: typing.Iterator[T],
                          parallel_quantity: int,
                          sleep_seconds: float = 0,
                          notify_action: typing.Callable[[int], None] = None,
                          error_action: typing.Callable[[BaseException], None] = None) -> typing.AsyncGenerator[tuple[S, T], None]:
    count = 0
    for chunk_instances in chunks(instances, parallel_quantity):
        try:
            if notify_action is not None and count % parallel_quantity == 0:
                notify_action(count)
            results = await asyncio.gather(
                *map(action, chunk_instances)
            )
            for result_pair in zip(results, chunk_instances):
                count += 1
                yield result_pair
            await asyncio.sleep(sleep_seconds)
        except asyncio.CancelledError:
            count += len(chunk_instances)
            print("stop iteration")
            # raise StopIteration()
            raise StopAsyncIteration()
            # break
        except BaseException as err:
            count += len(chunk_instances)
            if error_action:
                error_action(err)
            else:
                raise err

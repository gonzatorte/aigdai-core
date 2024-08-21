import typing
import asyncio
from timeit import default_timer as timer
from collections.abc import Iterator
from typing import AsyncIterator

L = typing.TypeVar('L')

async def chunks_async(lst: typing.AsyncIterator[L], n: int):
    rr = []
    async for item in lst:
        rr.append(item)
        if len(rr) == n:
            yield rr
            rr = []
    yield rr


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

class PeepIterator(Iterator):
    def __init__(self, it):
        self.it = iter(it)
        self._hasnext = None
    def __iter__(self):
        return self
    def __next__(self):
        if self._hasnext:
            result = self._thenext
        else:
            result = next(self.it)
        self._hasnext = None
        return result
    def hasnext(self):
        if self._hasnext is None:
            try:
                self._thenext = next(self.it)
            except StopIteration:
                self._hasnext = False
            else:
                self._hasnext = True
        return self._hasnext


class AsyncPeepIterator(AsyncIterator):
    def __init__(self, it):
        self.it = aiter(it)
        self._hasnext = None
    def __iter__(self):
        return self
    async def __anext__(self):
        if self._hasnext:
            result = self._thenext
        else:
            result = await anext(self.it)
        self._hasnext = None
        return result
    async def hasnext(self):
        if self._hasnext is None:
            try:
                self._thenext = await anext(self.it)
            except StopIteration:
                self._hasnext = False
            except StopAsyncIteration:
                self._hasnext = False
            else:
                self._hasnext = True
        return self._hasnext

async def run_in_block(action: typing.Callable[[T], S], instances: typing.Iterator[T] | typing.AsyncIterator[L],
parallel_quantity: int, sleep_seconds: float = 0, notify_action: typing.Callable[[int], None] = None,
                          error_action: typing.Callable[[BaseException, typing.Optional[typing.Any]], None] = None) -> typing.AsyncGenerator[list[tuple[S, T]], None]:
    is_async = hasattr(instances, '__anext__') and callable(instances.__anext__)
    if is_async:
        chunk_iterator = chunks_async(instances, parallel_quantity)
    else:
        chunk_iterator = chunks(instances, parallel_quantity)
    count = 0
    while True:
        try:
            if is_async:
                chunk = await anext(chunk_iterator)
            else:
                chunk = next(chunk_iterator)
        except StopAsyncIteration:
            break
        except StopIteration:
            break
        try:
            if notify_action is not None and count % parallel_quantity == 0:
                notify_action(count)
            results = await asyncio.gather(
                *map(action, chunk)
            )
            start_time = timer()
            yield zip(results, chunk)
            has_next = True
            if hasattr(instances, 'hasnext') and callable(instances.hasnext):
                has_next = await instances.hasnext()
            if has_next:
                end_time = timer()
                elapsed = end_time - start_time
                if sleep_seconds - elapsed > 0:
                    await asyncio.sleep(sleep_seconds - elapsed)
            count += len(chunk)
        except asyncio.CancelledError:
            print("stop iteration")
            # raise StopIteration()
            raise StopAsyncIteration()
        except StopAsyncIteration:
            break
        except GeneratorExit:
            break
        except BaseException as err:
            count += len(chunk)
            if error_action:
                should_skip = error_action(err, chunk)
                print('should_skip', should_skip)
                if should_skip:
                    continue
            else:
                raise err

async def run_in_parallel(action: typing.Callable[[T], S], instances: typing.Iterator[T],
                          parallel_quantity: int,
                          sleep_seconds: float = 0,
                          notify_action: typing.Callable[[int], None] = None,
                          error_action: typing.Callable[[BaseException], None] = None) -> typing.AsyncGenerator[tuple[S, T], None]:
    async for block in run_in_block(action, instances, parallel_quantity, sleep_seconds, notify_action, error_action):
        for result_pair in block:
            yield result_pair

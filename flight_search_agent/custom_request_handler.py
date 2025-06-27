import asyncio
import logging
from typing import AsyncGenerator, cast

from a2a.server.context import ServerCallContext
from a2a.server.events import Event, EventConsumer, EventQueue
from a2a.server.tasks import PushNotifier, ResultAggregator, TaskManager
from a2a.types import (
    InternalError,
    MessageSendConfiguration,
    MessageSendParams,
    PushNotificationConfig,
    Task,
    TaskState,
    TaskStatus,
)
from a2a.utils.errors import ServerError

from a2a.server.request_handlers import DefaultRequestHandler


logger = logging.getLogger(__name__)


class CustomRequestHandler(DefaultRequestHandler):
    """Custom request handler that extends DefaultRequestHandler.
    
    This handler maintains all default functionality while providing
    custom implementation for the streaming message send method.
    """

    async def on_message_send_stream(
        self,
        params: MessageSendParams,
        context: ServerCallContext | None = None,
    ) -> AsyncGenerator[Event]:
        """Custom handler for 'message/stream' (streaming).

        Starts the agent execution and yields events as they are produced
        by the agent.
        """
        task_manager = TaskManager(
            task_id=params.message.taskId,
            context_id=params.message.contextId,
            task_store=self.task_store,
            initial_message=params.message,
        )
        task = Task(
            id=params.message.taskId,
            contextId=params.message.contextId,
            status=TaskStatus(
                state=TaskState.submitted,
            )
        )
        task = await task_manager.save_task_event(task)
        task: Task | None = await task_manager.get_task()

        if task:
            task = task_manager.update_with_message(params.message, task)

            if self.should_add_push_info(params):
                assert isinstance(self._push_notifier, PushNotifier)
                assert isinstance(
                    params.configuration, MessageSendConfiguration
                )
                assert isinstance(
                    params.configuration.pushNotificationConfig,
                    PushNotificationConfig,
                )
                await self._push_notifier.set_info(
                    task.id, params.configuration.pushNotificationConfig
                )
        else:
            queue = EventQueue()
        result_aggregator = ResultAggregator(task_manager)
        request_context = await self._request_context_builder.build(
            params=params,
            task_id=task.id if task else None,
            context_id=params.message.contextId,
            task=task,
            context=context,
        )

        task_id = cast('str', request_context.task_id)
        queue = await self._queue_manager.create_or_tap(task_id)
        producer_task = asyncio.create_task(
            self._run_event_stream(
                request_context,
                queue,
            )
        )
        await self._register_producer(task_id, producer_task)

        try:
            consumer = EventConsumer(queue)
            producer_task.add_done_callback(consumer.agent_task_callback)
            async for event in result_aggregator.consume_and_emit(consumer):
                if isinstance(event, Task):
                    if task_id != event.id:
                        logger.error(
                            f'Agent generated task_id={event.id} does not match the RequestContext task_id={task_id}.'
                        )
                        raise ServerError(
                            InternalError(
                                message='Task ID mismatch in agent response'
                            )
                        )

                    if (
                        self._push_notifier
                        and params.configuration
                        and params.configuration.pushNotificationConfig
                    ):
                        await self._push_notifier.set_info(
                            task_id,
                            params.configuration.pushNotificationConfig,
                        )

                if self._push_notifier and task_id:
                    latest_task = await result_aggregator.current_result
                    if isinstance(latest_task, Task):
                        await self._push_notifier.send_notification(latest_task)
                yield event
        except Exception as e:
            print(f"❌ {e}")
        finally:
            await self._cleanup_producer(producer_task, task_id) 

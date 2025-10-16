/**
 * Copyright 2023 Vercel, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

'use client';;
import { Button } from '@repo/shadcn-ui/components/ui/button';
import { cn } from '@repo/shadcn-ui/lib/utils';
import { ArrowDownIcon } from 'lucide-react';
import { useCallback } from 'react';
import { StickToBottom, useStickToBottomContext } from 'use-stick-to-bottom';

export const Conversation = ({
  className,
  ...props
}) => (
  <StickToBottom
    className={cn('relative flex-1 overflow-y-auto', className)}
    initial="smooth"
    resize="smooth"
    role="log"
    {...props} />
);

export const ConversationContent = ({
  className,
  ...props
}) => (
  <StickToBottom.Content className={cn('p-4', className)} {...props} />
);

export const ConversationScrollButton = ({
  className,
  ...props
}) => {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();

  const handleScrollToBottom = useCallback(() => {
    scrollToBottom();
  }, [scrollToBottom]);

  return (!isAtBottom && (<Button
    className={cn('absolute bottom-4 left-[50%] translate-x-[-50%] rounded-full', className)}
    onClick={handleScrollToBottom}
    size="icon"
    type="button"
    variant="outline"
    {...props}>
    <ArrowDownIcon className="size-4" />
  </Button>));
};

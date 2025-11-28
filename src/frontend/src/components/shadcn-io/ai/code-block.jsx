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
import { CheckIcon, CopyIcon } from 'lucide-react';
import { createContext, useContext, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import oneDark from "react-syntax-highlighter/dist/esm/styles/prism/one-dark";
import oneLight from "react-syntax-highlighter/dist/esm/styles/prism/one-light";


const CodeBlockContext = createContext({
  code: '',
});

export const CodeBlock = ({
  code,
  language,
  showLineNumbers = false,
  className,
  children,
  ...props
}) => (
  <CodeBlockContext.Provider value={{ code }}>
    <div
      className={cn(
        'relative w-full overflow-hidden rounded-md border bg-background text-foreground',
        className
      )}
      {...props}>
      <div className="relative">
        <SyntaxHighlighter
          className="overflow-hidden dark:hidden"
          codeTagProps={{
            className: 'font-mono text-sm',
          }}
          customStyle={{
            margin: 0,
            padding: '1rem',
            fontSize: '0.875rem',
            background: 'hsl(var(--background))',
            color: 'hsl(var(--foreground))',
          }}
          language={language}
          lineNumberStyle={{
            color: 'hsl(var(--muted-foreground))',
            paddingRight: '1rem',
            minWidth: '2.5rem',
          }}
          showLineNumbers={showLineNumbers}
          style={oneLight}>
          {code}
        </SyntaxHighlighter>
        <SyntaxHighlighter
          className="hidden overflow-hidden dark:block"
          codeTagProps={{
            className: 'font-mono text-sm',
          }}
          customStyle={{
            margin: 0,
            padding: '1rem',
            fontSize: '0.875rem',
            background: 'hsl(var(--background))',
            color: 'hsl(var(--foreground))',
          }}
          language={language}
          lineNumberStyle={{
            color: 'hsl(var(--muted-foreground))',
            paddingRight: '1rem',
            minWidth: '2.5rem',
          }}
          showLineNumbers={showLineNumbers}
          style={oneDark}>
          {code}
        </SyntaxHighlighter>
        {children && (
          <div className="absolute top-2 right-2 flex items-center gap-2">
            {children}
          </div>
        )}
      </div>
    </div>
  </CodeBlockContext.Provider>
);

export const CodeBlockCopyButton = ({
  onCopy,
  onError,
  timeout = 2000,
  children,
  className,
  ...props
}) => {
  const [isCopied, setIsCopied] = useState(false);
  const { code } = useContext(CodeBlockContext);

  const copyToClipboard = async () => {
    if (typeof window === 'undefined' || !navigator.clipboard.writeText) {
      onError?.(new Error('Clipboard API not available'));
      return;
    }

    try {
      await navigator.clipboard.writeText(code);
      setIsCopied(true);
      onCopy?.();
      setTimeout(() => setIsCopied(false), timeout);
    } catch (error) {
      onError?.(error);
    }
  };

  const Icon = isCopied ? CheckIcon : CopyIcon;

  return (
    <Button
      className={cn('shrink-0', className)}
      onClick={copyToClipboard}
      size="icon"
      variant="ghost"
      {...props}>
      {children ?? <Icon size={14} />}
    </Button>
  );
};

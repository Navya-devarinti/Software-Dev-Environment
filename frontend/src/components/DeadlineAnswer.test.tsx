// @vitest-environment jsdom

import React, { act } from 'react';
import { Simulate } from 'react-dom/test-utils';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import DeadlineAnswer from './DeadlineAnswer';

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

const roots: Root[] = [];

async function render(element: React.ReactNode): Promise<HTMLElement> {
  const container = document.createElement('div');
  document.body.append(container);
  const root = createRoot(container);
  roots.push(root);
  await act(async () => root.render(element));
  return container;
}

afterEach(async () => {
  await act(async () => {
    roots.splice(0).forEach((root) => root.unmount());
  });
  document.body.innerHTML = '';
  vi.restoreAllMocks();
});

describe('DeadlineAnswer', () => {
  it('shows verified deadline text with source title, URL, and locator', async () => {
    const view = await render(
      <DeadlineAnswer
        response={{
          outcome: 'answered',
          message: 'For Fall 2026, the add/drop deadline is October 1, 2026.',
          citations: [
            {
              title: 'Academic Schedule',
              url: 'https://www.pnw.edu/registrar/schedule/',
              locator: 'Fall 2026, Add/Drop table row',
            },
          ],
        }}
      />,
    );

    expect(view.textContent).toContain('Fall 2026');
    expect(view.textContent).toContain('Academic Schedule');
    expect(view.textContent).toContain('Fall 2026, Add/Drop table row');
    expect(view.querySelector('a')?.getAttribute('href')).toBe(
      'https://www.pnw.edu/registrar/schedule/',
    );
  });

  it('makes a missing-term clarification prominent', async () => {
    const view = await render(
      <DeadlineAnswer
        response={{
          outcome: 'needs_context',
          message: 'Which academic term do you mean?',
          requiredContext: ['term'],
        }}
      />,
    );

    expect(view.querySelector('h2')?.textContent).toBe('Which academic term do you mean?');
    expect(view.textContent).toContain('Which academic term do you mean?');
  });

  it('shows a safe referral without unsupported dates, conditions, or deadline citations', async () => {
    const view = await render(
      <DeadlineAnswer
        response={{
          outcome: 'escalation_required',
          message: 'The deadline is October 1, 2026, if you withdraw before noon.',
          citations: [
            {
              title: 'Schedule',
              url: 'https://www.pnw.edu/schedule/',
              locator: 'October 1 deadline',
            },
          ],
          escalation: {
            office: 'Registrar',
            reason: 'The October 1 date may apply if you act before noon.',
            contactUrl: 'https://www.pnw.edu/registrar/',
          },
        }}
      />,
    );

    expect(view.textContent).toContain('Registrar');
    expect(view.textContent).toContain("I can't verify a current, complete deadline.");
    expect(view.textContent).not.toContain('October 1');
    expect(view.textContent).not.toContain('before noon');
    expect(view.querySelector('a')?.getAttribute('href')).toBe(
      'https://www.pnw.edu/registrar/',
    );
  });

  it('abstains when an answer is missing complete source details', async () => {
    const view = await render(
      <DeadlineAnswer
        response={{
          outcome: 'answered',
          message: 'The deadline is October 1, 2026.',
          citations: [{ title: 'Academic Schedule' }],
        }}
      />,
    );

    expect(view.querySelector('h2')?.textContent).toBe('Deadline not verified');
    expect(view.textContent).not.toContain('October 1, 2026');
    expect(view.textContent).toContain('Academic Schedule');
  });

  it('submits the question and optional term through the chat API', async () => {
    const result = {
      outcome: 'needs_context',
      message: 'Which academic term do you mean?',
      requiredContext: ['term'],
      citations: [],
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => result,
    });
    vi.stubGlobal('fetch', fetchMock);
    const view = await render(<App />);

    await act(async () => {
      const questionInput = view.querySelector('textarea')!;
      questionInput.value = 'When is add/drop?';
      Simulate.change(questionInput);
      const termInput = view.querySelector('input')!;
      termInput.value = 'Fall 2026';
      Simulate.change(termInput);
    });
    await act(async () => {
      Simulate.submit(view.querySelector('form')!);
    });

    expect(fetchMock).toHaveBeenCalledWith(
      '/v1/chat',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          question: 'When is add/drop?',
          context: { term: 'Fall 2026' },
        }),
      }),
    );
    expect(view.textContent).toContain('Which academic term do you mean?');
  });
});

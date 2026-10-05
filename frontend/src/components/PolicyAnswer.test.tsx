// @vitest-environment jsdom

import React, { act } from 'react';
import { Simulate } from 'react-dom/test-utils';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import PolicyAnswer from './PolicyAnswer';

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

describe('PolicyAnswer', () => {
  it('renders an answered policy explanation with citations', async () => {
    const view = await render(
      <PolicyAnswer
        response={{
          outcome: 'answered',
          message: 'Pay online through the PNW Parking Portal using the citation number. Next steps: Pay online through the PNW Parking Portal.',
          citations: [
            {
              title: 'Pay a Parking Citation',
              url: 'https://www.pnw.edu/parking/pay-citation/',
              locator: 'Payment instructions',
            },
            {
              title: 'Parking Citation Appeal Instructions',
              url: 'https://www.pnw.edu/parking/documents/citation-appeal.pdf',
              locator: 'PDF page 2, Appeal submission',
            },
          ],
        }}
      />,
    );

    expect(view.textContent).toContain('Pay online through the PNW Parking Portal');
    expect(view.textContent).toContain('Next steps: Pay online through the PNW Parking Portal.');
    expect(view.textContent).toContain('Pay a Parking Citation');
    expect(view.textContent).toContain('Payment instructions');
    expect(view.textContent).toContain('Parking Citation Appeal Instructions');
    expect(view.textContent).toContain('PDF page 2, Appeal submission');
    expect(view.querySelectorAll('a').length).toBeGreaterThanOrEqual(2);
  });

  it('renders child-page and PDF citations with clickable URLs and locators', async () => {
    const view = await render(
      <PolicyAnswer
        response={{
          outcome: 'answered',
          message: 'Follow the linked instructions for the parking citation.',
          citations: [
            {
              title: 'Parking Services',
              url: 'https://www.pnw.edu/parking/',
              locator: 'Parking citations section',
            },
            {
              title: 'Parking Citation Appeal Instructions',
              url: 'https://www.pnw.edu/parking/documents/citation-appeal.pdf',
              locator: 'PDF page 2, Appeal submission',
            },
          ],
        }}
      />,
    );

    const links = Array.from(view.querySelectorAll('a')).map((node) => node.getAttribute('href'));
    expect(links).toContain('https://www.pnw.edu/parking/');
    expect(links).toContain('https://www.pnw.edu/parking/documents/citation-appeal.pdf');
    expect(view.textContent).toContain('Parking citations section');
    expect(view.textContent).toContain('PDF page 2, Appeal submission');
  });

  it('renders escalation_required with office, reason, contact link, and general guidance', async () => {
    const view = await render(
      <PolicyAnswer
        response={{
          outcome: 'escalation_required',
          message: 'General published guidance: Submit an appeal within 10 calendar days of the citation. I can\'t determine an individual outcome. Please contact Parking Services for a decision about your situation.',
          citations: [
            {
              title: 'Parking Citation Appeal Instructions',
              url: 'https://www.pnw.edu/parking/documents/citation-appeal.pdf',
              locator: 'PDF page 2, Appeal submission',
            },
          ],
          escalation: {
            office: 'Parking Services',
            reason: 'Parking Services handles parking citation appeals.',
            contactUrl: 'https://www.pnw.edu/parking/',
          },
        }}
      />,
    );

    expect(view.textContent).toContain('Contact the responsible office');
    expect(view.textContent).toContain('Parking Services');
    expect(view.textContent).toContain("I can't determine an individual outcome");
    expect(view.textContent).toContain('Parking Services handles parking citation appeals.');
    expect(view.querySelector('a')?.getAttribute('href')).toBe('https://www.pnw.edu/parking/');
  });

  it('does not present an individual approval or denial decision in escalation UI', async () => {
    const view = await render(
      <PolicyAnswer
        response={{
          outcome: 'escalation_required',
          message: 'General published guidance: Submit an appeal within 10 calendar days of the citation. I can\'t determine an individual outcome. Please contact Parking Services for a decision about your situation.',
          citations: [
            {
              title: 'Parking Citation Appeal Instructions',
              url: 'https://www.pnw.edu/parking/documents/citation-appeal.pdf',
              locator: 'PDF page 2, Appeal submission',
            },
          ],
          escalation: {
            office: 'Parking Services',
            reason: 'Parking Services handles parking citation appeals.',
            contactUrl: 'https://www.pnw.edu/parking/',
          },
        }}
      />,
    );

    expect(view.textContent).not.toContain('will be approved');
    expect(view.textContent).not.toContain('approved');
    expect(view.textContent).not.toContain('denied');
    expect(view.textContent).not.toContain('waived');
  });

  it('renders cannot_verify safely', async () => {
    const view = await render(
      <PolicyAnswer
        response={{
          outcome: 'cannot_verify',
          message: "I can't verify a current, complete policy or procedure from reliable official evidence.",
          citations: [],
        }}
      />,
    );

    expect(view.textContent).toContain("I can't verify a current, complete policy or procedure");
    expect(view.textContent).toContain('Policy not verified');
  });

  it('renders needs_context safely', async () => {
    const view = await render(
      <PolicyAnswer
        response={{
          outcome: 'needs_context',
          message: 'I need the campus and relevant policy context before I can answer accurately.',
          requiredContext: ['campus'],
        }}
      />,
    );

    expect(view.textContent).toContain('More context needed');
    expect(view.textContent).toContain('campus');
  });

  it('routes a clear policy question to PolicyAnswer in App', async () => {
    const result = {
      outcome: 'answered',
      message: 'Pay online through the PNW Parking Portal using the citation number. Next steps: Pay online through the PNW Parking Portal.',
      citations: [
        {
          title: 'Pay a Parking Citation',
          url: 'https://www.pnw.edu/parking/pay-citation/',
          locator: 'Payment instructions',
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => result,
    });
    vi.stubGlobal('fetch', fetchMock);

    const view = await render(<App />);
    const questionInput = view.querySelector('textarea')!;
    const form = view.querySelector('form')!;

    await act(async () => {
      questionInput.value = 'How do I pay a parking citation?';
      Simulate.change(questionInput);
    });

    await act(async () => {
      Simulate.submit(form);
    });

    expect(view.textContent).toContain('Policy guidance');
    expect(view.textContent).toContain('Pay online through the PNW Parking Portal');
    expect(fetchMock).toHaveBeenCalled();
  });
});

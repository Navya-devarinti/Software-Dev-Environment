// @vitest-environment jsdom

import React, { act } from 'react';
import { Simulate } from 'react-dom/test-utils';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import AcademicAnswer from './AcademicAnswer';

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

describe('AcademicAnswer', () => {
  it('renders supported academic guidance, citations, and next steps', async () => {
    const view = await render(
      <AcademicAnswer
        response={{
          outcome: 'answered',
          message: 'Computer Science requirements are listed in the catalog.',
          citations: [
            {
              title: 'PNW Academic Catalog',
              url: 'https://www.pnw.edu/academic-catalog/',
              locator: 'Computer Science requirements',
            },
          ],
          nextSteps: ['Review the published program requirements.'],
        }}
      />,
    );

    expect(view.textContent).toContain('Computer Science requirements');
    expect(view.textContent).toContain('PNW Academic Catalog');
    expect(view.textContent).toContain('Computer Science requirements');
    expect(view.textContent).toContain('Next steps');
    expect(view.querySelector('a')?.getAttribute('href')).toBe(
      'https://www.pnw.edu/academic-catalog/',
    );
  });

  it('does not make unsafe citation URLs clickable', async () => {
    const view = await render(
      <AcademicAnswer
        response={{
          outcome: 'answered',
          message: 'Published program requirements are available.',
          citations: [
            {
              title: 'Catalog',
              url: 'javascript:alert(1)',
              locator: 'Program requirements',
            },
          ],
        }}
      />,
    );

    expect(view.querySelector('a')).toBeNull();
    expect(view.textContent).toContain('javascript:alert(1)');
  });

  it('shows a clarification for missing academic context', async () => {
    const view = await render(
      <AcademicAnswer
        response={{
          outcome: 'needs_context',
          message: 'Which program do you mean?',
          requiredContext: ['program', 'studentId'],
        }}
      />,
    );

    expect(view.textContent).toContain('Which program do you mean?');
    expect(view.textContent).toContain('program');
    expect(view.textContent).not.toContain('studentId');
  });

  it('displays Academic Advising escalation without an individual determination', async () => {
    const view = await render(
      <AcademicAnswer
        response={{
          outcome: 'escalation_required',
          message: 'You will graduate. Contact an advisor.',
          escalation: {
            office: 'Academic Advising',
            reason: 'An advisor must review individual graduation eligibility.',
            contactUrl: 'https://www.pnw.edu/advising/',
          },
          citations: [],
        }}
      />,
    );

    expect(view.textContent).toContain('Academic advising referral');
    expect(view.textContent).toContain('Academic Advising');
    expect(view.textContent).toContain("I can't determine an individual");
    expect(view.textContent).not.toContain('You will graduate');
    expect(view.querySelector('a')?.getAttribute('href')).toBe(
      'https://www.pnw.edu/advising/',
    );
  });

  it('shows a non-definitive state when academic evidence cannot be verified', async () => {
    const view = await render(
      <AcademicAnswer
        response={{
          outcome: 'cannot_verify',
          message: "I can't verify a complete, current academic answer.",
          citations: [],
        }}
      />,
    );

    expect(view.textContent).toContain('Academic information not verified');
    expect(view.textContent).toContain("can't verify");
  });

  it('routes a general academic question to AcademicAnswer in App', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        outcome: 'answered',
        message: 'Computer Science requirements are listed in the catalog.',
        citations: [
          {
            title: 'PNW Academic Catalog',
            url: 'https://www.pnw.edu/academic-catalog/',
            locator: 'Computer Science requirements',
          },
        ],
      }),
    });
    vi.stubGlobal('fetch', fetchMock);
    const view = await render(<App />);

    await act(async () => {
      const questionInput = view.querySelector('textarea')!;
      questionInput.value = 'What are the Computer Science degree requirements?';
      Simulate.change(questionInput);
    });
    await act(async () => {
      Simulate.submit(view.querySelector('form')!);
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(view.textContent).toContain('Academic guidance');
    expect(view.textContent).toContain('PNW Academic Catalog');
    expect(view.textContent).not.toContain('Deadline information');
  });
});

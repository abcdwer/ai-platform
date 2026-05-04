/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '@/components/ui/input';

describe('Input Component', () => {
  it('renders input element', () => {
    render(<Input />);
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
  });

  it('renders with placeholder', () => {
    render(<Input placeholder="Enter text..." />);
    const input = screen.getByPlaceholderText('Enter text...');
    expect(input).toBeInTheDocument();
  });

  it('renders with default value', () => {
    render(<Input defaultValue="Initial value" />);
    const input = screen.getByDisplayValue('Initial value');
    expect(input).toBeInTheDocument();
  });

  it('handles text changes', () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'new value' } });
    
    expect(handleChange).toHaveBeenCalled();
  });

  it('accepts custom className', () => {
    const { container } = render(<Input className="custom-input-class" />);
    const input = container.querySelector('input');
    expect(input).toHaveClass('custom-input-class');
  });

  it('renders disabled input', () => {
    render(<Input disabled placeholder="Disabled input" />);
    const input = screen.getByPlaceholderText('Disabled input');
    expect(input).toBeDisabled();
  });

  it('renders with type attribute', () => {
    render(<Input type="email" placeholder="email@example.com" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');
  });

  it('renders with different types', () => {
    const types = ['text', 'email', 'password', 'number', 'tel', 'url'];
    
    types.forEach((type) => {
      const { container } = render(<Input type={type as 'text' | 'email' | 'password' | 'number' | 'tel' | 'url'} />);
      const input = container.querySelector('input');
      expect(input).toHaveAttribute('type', type);
    });
  });
});

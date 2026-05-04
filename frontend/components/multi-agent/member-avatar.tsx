'use client';

import { MEMBER_ROLE_COLORS } from '@/types/multi-agent';
import type { AgentMember } from '@/types/multi-agent';
import { cn } from '@/lib/utils';

interface MemberAvatarProps {
  member: AgentMember;
  size?: 'sm' | 'md' | 'lg';
  showTooltip?: boolean;
}

const SIZE_CLASSES = {
  sm: 'w-6 h-6 text-xs',
  md: 'w-8 h-8 text-sm',
  lg: 'w-10 h-10 text-base',
};

export function MemberAvatar({ member, size = 'md', showTooltip = false }: MemberAvatarProps) {
  const color = member.color || MEMBER_ROLE_COLORS[member.role];
  
  return (
    <div
      className={cn(
        "rounded-full flex items-center justify-center text-white font-medium",
        SIZE_CLASSES[size]
      )}
      style={{ backgroundColor: color }}
      title={showTooltip ? `${member.name} (${member.role})` : undefined}
    >
      {member.icon ? (
        <span className="text-lg">{member.icon}</span>
      ) : (
        member.name.charAt(0).toUpperCase()
      )}
    </div>
  );
}

import React from 'react';
import { Avatar as ChakraAvatar, AvatarProps as ChakraAvatarProps } from '@chakra-ui/react';
import { User } from '../../types';

interface AvatarProps extends ChakraAvatarProps {
  user?: User | null;
}

export const Avatar: React.FC<AvatarProps> = ({ user, ...props }) => {
  const getInitials = (user: User) => {
    if (user.firstName && user.lastName) {
      return `${user.firstName.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();
    }
    if (user.username) {
      return user.username.charAt(0).toUpperCase();
    }
    return user.email.charAt(0).toUpperCase();
  };

  const getDisplayName = (user: User) => {
    if (user.firstName && user.lastName) {
      return `${user.firstName} ${user.lastName}`;
    }
    return user.username || user.email;
  };

  if (!user) {
    return (
      <ChakraAvatar
        name="Unknown User"
        src=""
        {...props}
      />
    );
  }

  return (
    <ChakraAvatar
      name={getDisplayName(user)}
      src={user.avatar}
      children={user.avatar ? undefined : getInitials(user)}
      {...props}
    />
  );
};
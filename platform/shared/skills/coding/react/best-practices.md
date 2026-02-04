# React Best Practices

> คู่มือ Best Practices สำหรับ React Development ใน WitMind.AI

## 1. Component Design

### ✅ DO: ใช้ Functional Components + Hooks
```tsx
// ✅ Good
export function UserProfile({ userId }: { userId: string }) {
  const { data: user, isLoading } = useUser(userId);

  if (isLoading) return <Skeleton />;
  return <div>{user.name}</div>;
}
```

### ❌ DON'T: ใช้ Class Components
```tsx
// ❌ Bad - Avoid class components
class UserProfile extends React.Component {
  // ...
}
```

## 2. State Management

### ✅ DO: ใช้ State ที่เหมาะสมกับ Scope

| Scope | Solution |
|-------|----------|
| Component-local | `useState` |
| Shared between few components | Lift state up + props |
| Complex component state | `useReducer` |
| Global UI state | Zustand / Jotai |
| Server state | TanStack Query |

### ✅ DO: Colocate State ใกล้ที่ใช้
```tsx
// ✅ Good - state อยู่ใน component ที่ใช้
function SearchBox() {
  const [query, setQuery] = useState('');
  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

## 3. Performance

### ✅ DO: Memoize เฉพาะเมื่อจำเป็น
```tsx
// ✅ Good - memo expensive computation
const sortedItems = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);

// ✅ Good - memo callback passed to child
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);
```

### ❌ DON'T: Premature Optimization
```tsx
// ❌ Bad - unnecessary memoization
const name = useMemo(() => `${firstName} ${lastName}`, [firstName, lastName]);
// Just use: const name = `${firstName} ${lastName}`;
```

## 4. Error Handling

### ✅ DO: ใช้ Error Boundaries
```tsx
// ✅ Good
<ErrorBoundary fallback={<ErrorPage />}>
  <App />
</ErrorBoundary>
```

### ✅ DO: Handle Loading และ Error States
```tsx
// ✅ Good
function UserList() {
  const { data, isLoading, error } = useUsers();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data?.length) return <EmptyState />;

  return <List items={data} />;
}
```

## 5. TypeScript

### ✅ DO: Type Props อย่างชัดเจน
```tsx
// ✅ Good
interface ButtonProps {
  variant: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
}

export function Button({ variant, size = 'md', children, onClick }: ButtonProps) {
  // ...
}
```

### ❌ DON'T: ใช้ any
```tsx
// ❌ Bad
function Component(props: any) { }

// ❌ Bad
const [data, setData] = useState<any>(null);
```

## 6. Accessibility

### ✅ DO: ใช้ Semantic HTML
```tsx
// ✅ Good
<button onClick={handleClick}>Submit</button>
<nav><ul><li><a href="/home">Home</a></li></ul></nav>

// ❌ Bad
<div onClick={handleClick}>Submit</div>
<div><div><div onClick={() => navigate('/home')}>Home</div></div></div>
```

### ✅ DO: เพิ่ม ARIA Labels
```tsx
// ✅ Good
<button aria-label="Close dialog" onClick={onClose}>
  <XIcon />
</button>

<input
  aria-label="Search products"
  aria-describedby="search-hint"
  placeholder="Search..."
/>
<span id="search-hint">Enter product name or SKU</span>
```

## 7. Testing

### ✅ DO: Test Behavior ไม่ใช่ Implementation
```tsx
// ✅ Good - test what user sees
test('shows error message when login fails', async () => {
  render(<LoginForm />);

  await userEvent.type(screen.getByLabelText('Email'), 'test@test.com');
  await userEvent.type(screen.getByLabelText('Password'), 'wrong');
  await userEvent.click(screen.getByRole('button', { name: 'Login' }));

  expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
});
```

## 8. Folder Structure

```
src/
├── components/
│   ├── ui/                 # Primitive UI components
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts
│   │   └── Input/
│   ├── features/           # Feature-specific components
│   │   ├── auth/
│   │   └── dashboard/
│   └── layout/             # Layout components
├── hooks/                  # Custom hooks
├── lib/                    # Utilities
├── services/               # API services
├── stores/                 # State management
└── types/                  # TypeScript types
```

## 9. Import Order

```tsx
// 1. React
import { useState, useEffect } from 'react';

// 2. External libraries
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';

// 3. Internal modules (absolute imports)
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';

// 4. Relative imports
import { UserAvatar } from './UserAvatar';
import type { UserProfileProps } from './types';

// 5. Styles/Assets
import styles from './UserProfile.module.css';
```

## 10. Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase with use | `useAuth.ts` |
| Utilities | camelCase | `formatDate.ts` |
| Constants | SCREAMING_SNAKE | `API_BASE_URL` |
| Types/Interfaces | PascalCase | `UserProfile` |
| CSS Modules | camelCase | `styles.container` |
| Test files | .test.tsx | `Button.test.tsx` |

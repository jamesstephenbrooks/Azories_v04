import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  FiUsers, FiUserPlus, FiX, FiCheck, FiCopy, FiMail, 
  FiEdit3, FiEye, FiStar, FiTrash2 
} from 'react-icons/fi';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

// Role definitions
const ROLES = {
  owner: { name: 'Owner', icon: FiStar, color: 'text-yellow-500', permissions: ['read', 'write', 'manage', 'delete'] },
  editor: { name: 'Editor', icon: FiEdit3, color: 'text-blue-500', permissions: ['read', 'write'] },
  viewer: { name: 'Viewer', icon: FiEye, color: 'text-gray-500', permissions: ['read'] }
};

export default function CollaborativeWriting({ bookId, isOwner, currentCollaborators = [], onUpdate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [collaborators, setCollaborators] = useState(currentCollaborators);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('editor');
  const [isLoading, setIsLoading] = useState(false);
  const [inviteLink, setInviteLink] = useState('');

  useEffect(() => {
    setCollaborators(currentCollaborators);
  }, [currentCollaborators]);

  const generateInviteLink = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/api/books/${bookId}/invite-link`, {
        role: inviteRole
      });
      setInviteLink(response.data.invite_link);
      toast.success('Invite link generated!');
    } catch (error) {
      toast.error('Failed to generate invite link');
    } finally {
      setIsLoading(false);
    }
  };

  const sendInvite = async () => {
    if (!inviteEmail.trim()) return;

    try {
      setIsLoading(true);
      await axios.post(`${API}/api/books/${bookId}/invite`, {
        email: inviteEmail.trim(),
        role: inviteRole
      });
      toast.success(`Invitation sent to ${inviteEmail}`);
      setInviteEmail('');
      fetchCollaborators();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCollaborators = async () => {
    try {
      const response = await axios.get(`${API}/api/books/${bookId}/collaborators`);
      setCollaborators(response.data.collaborators || []);
      if (onUpdate) onUpdate(response.data.collaborators);
    } catch (error) {
      console.error('Failed to fetch collaborators:', error);
    }
  };

  const updateRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/api/books/${bookId}/collaborators/${userId}`, {
        role: newRole
      });
      toast.success('Role updated');
      fetchCollaborators();
    } catch (error) {
      toast.error('Failed to update role');
    }
  };

  const removeCollaborator = async (userId) => {
    if (!confirm('Remove this collaborator?')) return;

    try {
      await axios.delete(`${API}/api/books/${bookId}/collaborators/${userId}`);
      toast.success('Collaborator removed');
      fetchCollaborators();
    } catch (error) {
      toast.error('Failed to remove collaborator');
    }
  };

  const copyInviteLink = () => {
    navigator.clipboard.writeText(inviteLink);
    toast.success('Link copied to clipboard!');
  };

  if (!isOwner) return null;

  return (
    <>
      {/* Trigger Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="gap-2"
        data-testid="collab-trigger"
      >
        <FiUsers className="w-4 h-4" />
        Collaborators
        {collaborators.length > 0 && (
          <span className="ml-1 px-1.5 py-0.5 bg-primary text-primary-foreground text-xs rounded-full">
            {collaborators.length}
          </span>
        )}
      </Button>

      {/* Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              transition={{ duration: 0.2 }}
              className="bg-background rounded-2xl shadow-2xl max-w-md w-full max-h-[80vh] overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              {/* Header */}
              <div className="p-4 border-b flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                    <FiUsers className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <h2 className="font-bold">Collaborative Writing</h2>
                    <p className="text-xs text-muted-foreground">Invite others to write together</p>
                  </div>
                </div>
                <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-muted rounded-full">
                  <FiX className="w-5 h-5" />
                </button>
              </div>

              <div className="p-4 space-y-6 overflow-y-auto max-h-[60vh]">
                {/* Invite Section */}
                <div className="space-y-3">
                  <h3 className="font-medium text-sm">Invite by Email</h3>
                  <div className="flex gap-2">
                    <Input
                      type="email"
                      placeholder="email@example.com"
                      value={inviteEmail}
                      onChange={e => setInviteEmail(e.target.value)}
                      className="flex-1"
                    />
                    <select
                      value={inviteRole}
                      onChange={e => setInviteRole(e.target.value)}
                      className="px-3 py-2 bg-muted rounded-lg text-sm"
                    >
                      <option value="editor">Editor</option>
                      <option value="viewer">Viewer</option>
                    </select>
                    <Button onClick={sendInvite} disabled={isLoading || !inviteEmail.trim()}>
                      <FiUserPlus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Invite Link */}
                <div className="space-y-3">
                  <h3 className="font-medium text-sm">Or share a link</h3>
                  {inviteLink ? (
                    <div className="flex gap-2">
                      <Input value={inviteLink} readOnly className="flex-1 text-xs" />
                      <Button variant="outline" onClick={copyInviteLink}>
                        <FiCopy className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <Button variant="outline" onClick={generateInviteLink} disabled={isLoading} className="w-full">
                      Generate Invite Link
                    </Button>
                  )}
                </div>

                {/* Current Collaborators */}
                <div className="space-y-3">
                  <h3 className="font-medium text-sm">Current Collaborators</h3>
                  {collaborators.length === 0 ? (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No collaborators yet. Invite someone to start writing together!
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {collaborators.map(collab => {
                        const role = ROLES[collab.role] || ROLES.viewer;
                        const RoleIcon = role.icon;
                        
                        return (
                          <div 
                            key={collab.user_id} 
                            className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-medium">
                                {collab.name?.[0]?.toUpperCase() || collab.email?.[0]?.toUpperCase() || '?'}
                              </div>
                              <div>
                                <p className="text-sm font-medium">{collab.name || collab.email}</p>
                                <div className={`flex items-center gap-1 text-xs ${role.color}`}>
                                  <RoleIcon className="w-3 h-3" />
                                  <span>{role.name}</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2">
                              <select
                                value={collab.role}
                                onChange={e => updateRole(collab.user_id, e.target.value)}
                                className="px-2 py-1 bg-background border rounded text-xs"
                              >
                                <option value="editor">Editor</option>
                                <option value="viewer">Viewer</option>
                              </select>
                              <button 
                                onClick={() => removeCollaborator(collab.user_id)}
                                className="p-1.5 hover:bg-red-500/10 text-red-500 rounded"
                              >
                                <FiTrash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

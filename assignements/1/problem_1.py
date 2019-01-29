import numpy as np

from torch.utils.data import DataLoader
import torchvision.datasets as datasets
from torchvision import transforms

# TODO:
# - Refactor forward and backward methods to generalize to L layers
# - Enable script args input to easily run experiments with different hyperparameters
# - Add an extra dimension to W and X for the bias!


class NN(object):

    def __init__(self,
                 input_size=784,
                 output_size=10,
                 hidden_layers_size=[1024, 2048],
                 init='random',
                 lr=1.e-3):

        self.input_size = input_size
        self.hidden_layers_size = hidden_layers_size
        self.output_size = output_size
        self.lr = lr
        self.train = False

        self._initialize_weights(init)

    def _initialize_weights(self, init_method='random'):
        def _random(neurons_in, neurons_out):
            return np.random.normal(0, 0.01, (neurons_in, neurons_out))

        # Not super clean...
        init_weights = {
                'random': _random
                }

        sizes = [self.input_size] + self.hidden_layers_size + [self.output_size]
        self.W = [init_weights[init_method](sizes[i], sizes[i+1]) for i in range(len(sizes) - 1 )]

    def forward(self, X):
        h0 = X
        a1 = np.dot(self.W[0].T, h0)
        h1 = self._sigmoid(a1)
        a2 = np.dot(self.W[1].T, h1)
        h2 = self._sigmoid(a2)
        a3 = np.dot(self.W[2].T, h2)
        h3 = self._softmax(a3)

        cache = {
            'h0': h0,
            'a1': a1,
            'h1': h1,
            'a2': a2,
            'h2': h2,
            'a3': a3,
            'h3': h3,
            }

        return h3, cache

    def _sigmoid(self, X):
         return 1 / (1 + np.exp(-X))

    def _sigmoid_deriv(self, X):
        return self._sigmoid(X) * (1 - self._sigmoid(X))

    def _softmax(self, X):
        """ Softmax activation function """
        e_x = np.exp(X - np.max(X))
        return e_x / e_x.sum(axis=0)

    def loss(self, prediction, target):
        """ Cross-entropy loss """
        return -np.log((prediction * target).sum(axis=0)).mean()

    def backward(self, target, prediction, cache):
        grad_f = - (target - prediction)

        grad_W3 = np.dot(grad_f, cache['h2'].T)
        grad_b3 = grad_f
        grad_h2 = np.dot(self.W[2], grad_f)
        grad_a2 = np.multiply(grad_h2, self._sigmoid_deriv(cache['a2']))

        grad_W2 = np.dot(grad_a2, cache['h1'].T)
        grad_b2 = grad_a2
        grad_h1 = np.dot(self.W[1], grad_a2)
        grad_a1 = np.multiply(grad_h1, self._sigmoid_deriv(cache['a1']))

        grad_W1 = np.dot(grad_a1, cache['h0'].T)
        grad_b1 = grad_a1

        return [grad_W1.T, grad_W2.T, grad_W3.T]

    def update_weights(self, grads):
        if not self.train:
            raise Exception('You should not update weights while validating/testing')
        self.W = [self.W[i] - (self.lr * grads[i]) for i in range(len(self.W))]

    def training(self):
        self.train = True

    def eval(self):
        self.train = False


def load_dataset(batch_size, data_path='./data'):
    transform = transforms.Compose([transforms.ToTensor()])
    trainset = DataLoader(dataset=datasets.MNIST(root=data_path,
                                                 train=True,
                                                 download=True,
                                                 transform=transform),
                          batch_size=batch_size,
                          shuffle=True)
    testset = DataLoader(dataset=datasets.MNIST(root=data_path,
                                                train=False,
                                                download=True,
                                                transform=transform),
                         batch_size=batch_size,
                         shuffle=True)
    return trainset, testset


def preprocess(batch, n_class=10):
    """
    Transform model_input in flat vector and target in one-hot encoded
    """
    model_input, target = batch
    model_input = model_input.numpy().reshape((model_input.shape[0], -1)).T
    target_one_hot = np.zeros((n_class, target.shape[0]))
    target_one_hot[target, np.arange(target.shape[0])] = 1
    return model_input, target_one_hot


def main(model, trainset, validset, epochs):
    for epoch in range(epochs):
        # Training
        loss = 0
        model.training()
        for i, batch in enumerate(trainset):
            model_input, target = preprocess(batch)
            prediction, cache = model.forward(model_input)
            grads = model.backward(target, prediction, cache)
            model.update_weights(grads)
            loss += model.loss(prediction, target)
        print(f'Train loss={loss / (i + 1)} at epoch {epoch}')

        # Validation
        loss = 0
        model.eval()
        for i, batch in enumerate(validset):
            model_input, target = preprocess(batch)
            prediction, _ = model.forward(model_input)
            loss += model.loss(prediction, target)
        print(f'Valid loss={loss / (i + 1)} at epoch {epoch}')


if __name__ == '__main__':
    epochs = 10
    batch_size = 128

    model = NN()
    trainset, validset = load_dataset(batch_size)

    main(model=model,
         trainset=trainset,
         validset=validset,
         epochs=epochs)
